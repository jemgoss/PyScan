import sys
import socket
import httplib
import xml.dom.minidom
import sys

class hp_scan:
	_host = ""
	_port = 8080
	_http_client = 0

	_job_url = ""
	_image_width = 0
	_image_height = 0

	def __init__(self, host, port=8080):
		self._host = host
		self._port = port
		self._http_client = httplib.HTTPConnection(self._host, self._port)

	''' Communicates with the scanner and retrieves a raw scan '''
	def get_scan(self):

		self._walkup_scan()				# Get the scanner endpoint 
		status = self._scan_status()			# Check on the status of the scanner

		# Wait for our scanner to become idle
		while status != "Idle":
			print "[X] Current status of the scanner: " + status
			status = self._scan_status()				

		self._create_job()				# Create a job to scan the document	
		scan_data = self._get_scanned_document()	# Actually scan the document and return a raw image

		return scan_data

	def get_image_size(self):
		return (self._image_width, self._image_height)

	def _walkup_scan(self):
		try:
			self._http_client.connect()
			self._http_client.request("GET", "/WalkupScan/WalkupScanDestinations")

			http_response = self._http_client.getresponse()

			if http_response.status != 200:
				raise Exception("Expecting 200 response")

			http_data = http_response.read()
			http_response.close()


		except httplib.HTTPException:
			raise Exception("Could not send WalkUp request to scanner")


	# Retrieves the scanner status in string format 
	def _scan_status(self):
		try:
			self._http_client.connect()
			self._http_client.request("GET", "/Scan/Status")

			http_response = self._http_client.getresponse()

			xml_document = xml.dom.minidom.parseString(http_response.read())
			scanner_state = xml_document.getElementsByTagName("ScannerState")[0].firstChild.data

			http_response.close()

			return scanner_state

		except httplib.HTTPException:
			raise Exception("Could not send Status request to scanner")

	# Creates the scanner job with the specified parameters
	def _create_job(self, x_resolution=200, y_resolution=200, width=2550, height=3507):

		job_request = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
		job_request += "<ScanSettings xmlns=\"http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19 Scan Schema - 0.26.xsd\">"
		job_request += "<XResolution>%d</XResolution>" % (x_resolution)
		job_request += "<YResolution>%d</YResolution>" % (y_resolution)
		job_request += "<XStart>0</XStart>"
		job_request += "<YStart>0</YStart>"
		job_request += "<Width>%d</Width>" % (width)
		job_request += "<Height>%d</Height>" % (height)
		job_request += "<Format>Raw</Format>"
		job_request += "<CompressionQFactor>0</CompressionQFactor>"
		job_request += "<ColorSpace>Color</ColorSpace>"
		job_request += "<BitDepth>8</BitDepth>"
		job_request += "<InputSource>Platen</InputSource>"
		job_request += "<GrayRendering>NTSC</GrayRendering>"
		job_request += "<ToneMap>"
		job_request += "<Gamma>1000</Gamma>"
		job_request += "<Brightness>1000</Brightness>"
		job_request += "<Contrast>1000</Contrast>"
		job_request += "<Highlite>179</Highlite>"
		job_request += "<Shadow>25</Shadow>"
		job_request += "<Threshold>0</Threshold>"
		job_request += "</ToneMap>"
		job_request += "<SharpeningLevel>128</SharpeningLevel>"
		job_request += "<NoiseRemoval>0</NoiseRemoval>"
		job_request += "<ContentType>Photo</ContentType>"
		job_request += "</ScanSettings>\r\n"

		try:
			self._http_client.connect()
			self._http_client.putrequest("POST", "/Scan/Jobs")
			self._http_client.putheader("Content-Type", "text/xml")
			self._http_client.putheader("Content-Length", len(job_request) - 2)
			self._http_client.endheaders(message_body=job_request)

			http_response = self._http_client.getresponse()

			if http_response.status != 201:
				raise Exception("Error: Expecting 201 response")

			http_response.read()
			self._job_url = http_response.getheader("Location")

			http_response.close()

		except httplib.HTTPException:
			raise Exception("Could not send job to scanner")



	def cancel_scan(self):

		if self._job_url == "":
			return

		job_request = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
		job_request += "<Job xmlns=\"http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30 Jobs.xsd\">"
		job_request += "<JobUrl>%s</JobUrl>" % (self._job_url)
		job_request += "<JobState>Canceled</JobState>"
		job_request += "</Job>"
		
		self._http_client.connect()
		self._http_client.putrequest("PUT", "/Scan/Jobs")
		self._http_client.putheader("Content-Type", "text/xml")
		self._http_client.putheader("Content-Length", len(job_request) - 2)
		self._http_client.endheaders(message_body=job_request)

	def _get_scanned_document(self):

		try:
			self._http_client.connect()
			self._http_client.request("GET", self._job_url)

			http_response = self._http_client.getresponse()

			xml_response = xml.dom.minidom.parseString(http_response.read())

			binary_url = xml_response.getElementsByTagName("BinaryURL")[0].firstChild.data
			self._image_width = int(xml_response.getElementsByTagName("ImageWidth")[0].firstChild.data)
			self._image_height = int(xml_response.getElementsByTagName("ImageHeight")[0].firstChild.data)

			self._http_client.connect()
			self._http_client.request("GET", binary_url)

			http_response = self._http_client.getresponse()

			return http_response.read() 

		except httplib.HTTPException:
			raise "Cannot get scanned document"
			

if __name__ == "__main__":


	_pil_installed = False

	print "HP Deskjet 3070A Wifi Tool"
	print "Created by XPN (http://www.xpnsbraindump.com)\n"

	# Add auto-detection of IP address of printer
	# and converting resulting image to BMP

	if len(sys.argv) != 3:
		print "Usage: %s IP_ADDRESS_OF_SCANNER OUTPUT_DIR" % (sys.argv[0])
		quit()

	try:
		import Image
		_pil_installed = True
	except:
		# Image module not installed
		print "For the best experience, please install Python Imaging Library (http://www.pythonware.com/products/pil/)"
		print "For now, the image will be dumped in raw RGB format"
		_pil_installed = False

	try:
		scan = hp_scan(sys.argv[1])
		raw_image = scan.get_scan()

		if _pil_installed:
			image = Image.fromstring("RGB", scan.get_image_size(), raw_image)
			image.save(sys.argv[2] + "/output.bmp")

		else:
			fd = file.open(sys.argv[2] + "/output.raw", "w")
			fd.write(raw_image)
			fd.close()

	except KeyboardInterrupt:
		scan.cancel_scan()
