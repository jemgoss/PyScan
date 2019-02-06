import tkinter as tk

import http.client, urllib.parse
from http import HTTPStatus
import xml.dom.minidom
import sys
import os
import time

SCAN_REQUEST = """<?xml version="1.0"?>
<scan:ScanJob xmlns:scan="http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05">
  <scan:XResolution>{XResolution}</scan:XResolution>
  <scan:YResolution>{YResolution}</scan:YResolution>
  <scan:XStart>{XStart}</scan:XStart>
  <scan:YStart>{YStart}</scan:YStart>
  <scan:Width>{Width}</scan:Width>
  <scan:Height>{Height}</scan:Height>
  <scan:Format>Jpeg</scan:Format>
  <scan:CompressionQFactor>35</scan:CompressionQFactor>
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

CANCEL_REQUEST = """<?xml version="1.0" encoding="UTF-8"?>
<Job xmlns="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30 Jobs.xsd">"
<JobUrl>{job_url}</JobUrl>
<JobState>Canceled</JobState>
</Job>"""

scanToDir = os.getcwd()

class HpScan:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._http_conn = http.client.HTTPConnection(self._host, self._port)

    def get_scannerState(self):
        """ Return the scanner state. """
        print("GET", "/Scan/Status")
        self._http_conn.request("GET", "/Scan/Status")
        with self._http_conn.getresponse() as http_response:
            print(http_response.status, http_response.reason)
            if http_response.status != HTTPStatus.OK:
                raise Exception("Error sending Status request to scanner: " + http_response.reason)
            xml_document = xml.dom.minidom.parseString(http_response.read())
            return xml_document.getElementsByTagName("ScannerState")[0].firstChild.data

    def post_scan_job(self, width, height):
        print("POST", "/Scan/Jobs")
        self._http_conn.request("POST",
                                "/Scan/Jobs",
                                headers={ "Content-Type" : "text/xml" },
                                body=SCAN_REQUEST.format(
                                    XResolution=200,
                                    YResolution=200,
                                    XStart=0,
                                    YStart=0,
                                    Width=width,
                                    Height=height))
        with self._http_conn.getresponse() as http_response:
            print(http_response.status, http_response.reason)
            if http_response.status != HTTPStatus.CREATED:
                raise Exception("Error sending Scan job request to scanner: " + http_response.reason)
            http_response.read() # should be no content
            return http_response.getheader("Location")

    def get_jobState(self, job_url):
        """ Return the job state. """
        print("GET", job_url)
        self._http_conn.request("GET", job_url)
        with self._http_conn.getresponse() as http_response:
            print(http_response.status, http_response.reason)
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

    def get_upload(self, binaryURL, filename):
        print("GET", binaryURL)
        self._http_conn.request("GET", binaryURL)
        with self._http_conn.getresponse() as http_response:
            print(http_response.status, http_response.reason)
            with open(filename, "wb") as f:
                f.write(http_response.read())
                print("Saved image to:", filename)

    def get_scan(self, width, height, filename):
        print("Scanning:", width, height, filename)

        # Wait for our scanner to become idle
        while True:
            state = self.get_scannerState()
            if state == "Idle":
                break
            print("Current state of the scanner: " + state)
            time.sleep(5)

        job_url = self.post_scan_job(width, height)
        print("job_url", job_url)
        self._job_url = job_url # in case we want to query or cancel it later

        # Wait for the scan job to complete
        imageWidth = None
        imageHeight = None
        binaryURL = None
        while True:
            state, elem = self.get_jobState(job_url)
            pageState = None
            if elem:
                pageState = elem.getElementsByTagName("PageState")[0].firstChild.data
            print("Job state:", state, ", PageState:", pageState)
            if state == "Canceled" or state == "Completed":
                break
            if state == "Processing":
                if pageState and pageState == "ReadyToUpload":
                    imageWidth = int(elem.getElementsByTagName("ImageWidth")[0].firstChild.data)
                    imageHeight = int(elem.getElementsByTagName("ImageHeight")[0].firstChild.data)
                    binaryURL = elem.getElementsByTagName("BinaryURL")[0].firstChild.data
                    print("imageWidth:", imageWidth)
                    print("imageHeight:", imageHeight)
                    print("binaryURL:", binaryURL)
                    break
            time.sleep(5)

        if binaryURL:
            self.get_upload(binaryURL, filename)

            while True:
                state, elem = self.get_jobState(job_url)
                pageState = None
                if elem:
                    pageState = elem.getElementsByTagName("PageState")[0].firstChild.data
                print("Job state:", state, ", PageState:", pageState)
                if state == "Canceled" or state == "Completed":
                    break
                time.sleep(5)

    def cancel_scan(self):
        if self._job_url == "":
            return
        self._http_conn.request("PUT",
                                "/Scan/Jobs",
                                headers={ "Content-Type" : "text/xml" },
                                body=CANCEL_REQUEST.format(
                                    job_url=self._job_url))
        with self._http_conn.getresponse() as http_response:
            print(http_response.status, http_response.reason)
            print(http_response.read())

scan = HpScan(
    host="Printer.fios-router.home",
    port=80)

filename_entry = None

def get_filename():
    fn = filename_entry.get()
    if not fn:
        fn = time.strftime("%Y%m%d-%H%M%S")
    fn = os.path.join(scanToDir, fn + ".jpg")
    if os.path.exists(fn):
        raise Exception("File already exists: " + fn)
    return fn

def scan_5x3p5():
    scan.get_scan(1500, 1050, get_filename())

def scan_6x4():
    scan.get_scan(1800, 1200, get_filename())

def scan_7x5():
    scan.get_scan(2100, 1500, get_filename())

def scan_3p5x5():
    scan.get_scan(1050, 1500, get_filename())

def scan_4x6():
    scan.get_scan(1200, 1800, get_filename())

def scan_5x7():
    scan.get_scan(1500, 2100, get_filename())

def runGraphical():
    global filename_entry
    root = tk.Tk()
    root.title("Scan")

    row = tk.Frame(root)
    lab = tk.Label(row, width=15, text="Filename", anchor='w')
    filename_entry = tk.Entry(row)
    row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    lab.pack(side=tk.LEFT)
    filename_entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
    
    tk.Label(
        root,
        text="Landscape:").pack(side=tk.LEFT)

    tk.Button(
        root,
        text="Scan 5x3.5",
        command=scan_5x3p5).pack(side=tk.LEFT, padx=5, pady=5)

    tk.Button(
        root,
        text="Scan 6x4",
        command=scan_6x4).pack(side=tk.LEFT, padx=5, pady=5)

    tk.Button(
        root,
        text="Scan 7x5",
        command=scan_7x5).pack(side=tk.LEFT, padx=5, pady=5)

    tk.Label(
        root,
        text="Portrait:").pack(side=tk.LEFT)

    tk.Button(
        root,
        text="Scan 3.5x5",
        command=scan_3p5x5).pack(side=tk.LEFT, padx=5, pady=5)

    tk.Button(
        root,
        text="Scan 4x6",
        command=scan_4x6).pack(side=tk.LEFT, padx=5, pady=5)

    tk.Button(
        root,
        text="Scan 5x7",
        command=scan_5x7).pack(side=tk.LEFT, padx=5, pady=5)

    tk.Button(
        root,
        text='Quit',
        command=root.quit).pack(side=tk.RIGHT, padx=5, pady=5) # root.destroy

    root.mainloop()

if __name__ == "__main__":
    runGraphical()
