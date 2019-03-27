import tkinter as tk

import http.client, urllib.parse
from http import HTTPStatus
import xml.dom.minidom
import sys
import os
import time

RESOLUTION = 300
COMPRESSION_QFACTOR = 35

class HpScan:
    _SCAN_REQUEST = """<?xml version="1.0"?>
<scan:ScanJob xmlns:scan="http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05">
  <scan:XResolution>{XResolution}</scan:XResolution>
  <scan:YResolution>{YResolution}</scan:YResolution>
  <scan:XStart>{XStart}</scan:XStart>
  <scan:YStart>{YStart}</scan:YStart>
  <scan:Width>{Width}</scan:Width>
  <scan:Height>{Height}</scan:Height>
  <scan:Format>Jpeg</scan:Format>
  <scan:CompressionQFactor>{CompressionQFactor}</scan:CompressionQFactor>
  <scan:ColorSpace>Color</scan:ColorSpace>
  <scan:BitDepth>8</scan:BitDepth>
  <scan:InputSource>Platen</scan:InputSource>
  <scan:GrayRendering>NTSC</scan:GrayRendering>
  <scan:ToneMap>
    <scan:Gamma>1000</scan:Gamma>
    <scan:Brightness>1000</scan:Brightness>
    <scan:Contrast>1000</scan:Contrast>
    <scan:Highlite>179</scan:Highlite>
    <scan:Shadow>25</scan:Shadow>
  </scan:ToneMap>
  <scan:ContentType>Photo</scan:ContentType>
</scan:ScanJob>"""

    _CANCEL_REQUEST = """<?xml version="1.0" encoding="UTF-8"?>
<Job xmlns="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30 Jobs.xsd">"
<JobUrl>{job_url}</JobUrl>
<JobState>Canceled</JobState>
</Job>"""

    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._http_conn = http.client.HTTPConnection(self._host, self._port)

    def _get_scannerState(self):
        """ Return the scanner state. """
        #print("GET", "/Scan/Status")
        self._http_conn.request("GET", "/Scan/Status")
        with self._http_conn.getresponse() as http_response:
            #print(http_response.status, http_response.reason)
            if http_response.status != HTTPStatus.OK:
                raise Exception("Error sending Status request to scanner: " + http_response.reason)
            xml_document = xml.dom.minidom.parseString(http_response.read())
            return xml_document.getElementsByTagName("ScannerState")[0].firstChild.data

    def _post_scan_job(self, width, height, resolution):
        #print("POST", "/Scan/Jobs")
        self._http_conn.request("POST",
                                "/Scan/Jobs",
                                headers={ "Content-Type" : "text/xml" },
                                body=self._SCAN_REQUEST.format(
                                    XResolution=resolution,
                                    YResolution=resolution,
                                    XStart=0,
                                    YStart=0,
                                    Width=width,
                                    Height=height,
                                    CompressionQFactor=COMPRESSION_QFACTOR))
        with self._http_conn.getresponse() as http_response:
            #print(http_response.status, http_response.reason)
            if http_response.status != HTTPStatus.CREATED:
                raise Exception("Error sending Scan job request to scanner: " + http_response.reason)
            http_response.read() # should be no content
            return http_response.getheader("Location")

    def _get_jobState(self, job_url):
        """ Return the job state. """
        #print("GET", job_url)
        self._http_conn.request("GET", job_url)
        with self._http_conn.getresponse() as http_response:
            #print(http_response.status, http_response.reason)
            if http_response.status != HTTPStatus.OK:
                raise Exception("Error sending Job state request to scanner: " + http_response.reason)
            xml_document = xml.dom.minidom.parseString(http_response.read())
            jobState = xml_document.getElementsByTagName("j:JobState")[0].firstChild.data
            elem = None
            psp = xml_document.getElementsByTagName("PreScanPage")
            if psp:
                elem = psp[0]
            else:
                psp = xml_document.getElementsByTagName("PostScanPage")
                if psp:
                    elem = psp[0]
            return jobState, elem

    def _save_image(self, binaryURL, filename):
        #print("GET", binaryURL)
        self._http_conn.request("GET", binaryURL)
        with self._http_conn.getresponse() as http_response:
            #print(http_response.status, http_response.reason)
            with open(filename, "wb") as f:
                f.write(http_response.read())

    def do_scan(self, width, height, resolution, filename):
        print("Scanning:", width, height, resolution, filename)

        # Wait for our scanner to become idle
        print("Waiting for scanner to become ready...")
        while True:
            state = self._get_scannerState()
            if state == "Idle":
                break
            #print("Current state of the scanner: " + state)
            time.sleep(5)

        print("Scanning...")
        job_url = self._post_scan_job(width, height, resolution)
        #print("job_url", job_url)
        self._job_url = job_url # in case we want to query or cancel it later

        # Wait for the scan job to complete
        print("Waiting for scan job to complete...")
        imageWidth = None
        imageHeight = None
        binaryURL = None
        while True:
            state, elem = self._get_jobState(job_url)
            pageState = None
            if elem:
                pageState = elem.getElementsByTagName("PageState")[0].firstChild.data
            #print("Job state:", state, ", PageState:", pageState)
            if state == "Canceled" or state == "Completed":
                break
            if state == "Processing":
                if pageState and pageState == "ReadyToUpload":
                    imageWidth = int(elem.getElementsByTagName("ImageWidth")[0].firstChild.data)
                    imageHeight = int(elem.getElementsByTagName("ImageHeight")[0].firstChild.data)
                    binaryURL = elem.getElementsByTagName("BinaryURL")[0].firstChild.data
                    #print("imageWidth:", imageWidth)
                    #print("imageHeight:", imageHeight)
                    #print("binaryURL:", binaryURL)
                    break
            time.sleep(5)

        if binaryURL:
            print("Saving image to {}...".format(filename))
            self._save_image(binaryURL, filename)

            while True:
                state, elem = self._get_jobState(job_url)
                pageState = None
                if elem:
                    pageState = elem.getElementsByTagName("PageState")[0].firstChild.data
                #print("Job state:", state, ", PageState:", pageState)
                if state == "Canceled" or state == "Completed":
                    break
                time.sleep(5)
            print("Done")

    def cancel_scan(self):
        if self._job_url == "":
            return
        self._http_conn.request("PUT",
                                "/Scan/Jobs",
                                headers={ "Content-Type" : "text/xml" },
                                body=self._CANCEL_REQUEST.format(
                                    job_url=self._job_url))
        with self._http_conn.getresponse() as http_response:
            print(http_response.status, http_response.reason)
            print(http_response.read())

scan = HpScan(
    host="Printer.fios-router.home",
    port=80)

scanToDir = os.getcwd()

class Callback:
    def __init__(self, size, ent):
        self.size = size
        self.ent = ent
    def fn(self):
        dims = self.size.split("x")
        width = int(float(dims[0]) * RESOLUTION)
        height = int(float(dims[1]) * RESOLUTION)

        filename = self.ent.get()
        if not filename:
            filename = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(scanToDir, filename + ".jpg")
        if os.path.exists(filename):
            raise Exception("File already exists: " + filename)

        scan.do_scan(width, height, RESOLUTION, filename)

def runGraphical():
    root = tk.Tk()
    root.title("Scan")

    row = 0
    tk.Label(root, text="Filename:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
    ent = tk.Entry(root, width=12)
    ent.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
    row += 1

    for label, sizes in [
        ("Portrait:", ["3.5 x 5", "4 x 6", "5 x 7"]),
        ("Landscape:", ["5 x 3.5", "6 x 4", "7 x 5"])]:
        col = 0
        tk.Label(root, text=label).grid(row=row, column=col, sticky=tk.E, padx=5, pady=5)
        col += 1
        for size in sizes:
            tk.Button(root, text=size, command=Callback(size, ent).fn).grid(row=row, column=col, padx=5, pady=5)
            col += 1
        row += 1

    tk.Label(root, text="Custom size:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)

    custom = tk.Entry(root, width=8)
    custom.insert(0, "2 x 3")
    custom.grid(row=row, column=1, padx=5, pady=5)
    tk.Button(root, text="Scan", command=lambda: Callback(custom.get(), ent).fn()).grid(row=row, column=2, padx=5, pady=5)
    row += 1

    tk.Button(root, text='Quit', command=root.quit).grid(row=row, column=0, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    runGraphical()
