import http.client, urllib.parse
from http import HTTPStatus
import xml.dom.minidom

txt1 = """<?xml version="1.0" encoding="UTF-8"?>
<!-- THIS DATA SUBJECT TO DISCLAIMER(S) INCLUDED WITH THE PRODUCT OF ORIGIN. -->
<j:Job xmlns:j="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:fax="http://www.hp.com/schemas/imaging/con/fax/2008/06/13" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30 ../schemas/Jobs.xsd">
	<j:JobUrl>/Jobs/JobList/39</j:JobUrl>
	<j:JobCategory>Scan</j:JobCategory>
	<j:JobState>Processing</j:JobState>
	<j:JobStateUpdate>187-136</j:JobStateUpdate>
	<ScanJob xmlns="http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19">
   <PreScanPage>
     <PageNumber>1</PageNumber>
     <PageState>PreparingScan</PageState>
     <BufferInfo>
       <ScanSettings>
         <XResolution>200</XResolution>
         <YResolution>200</YResolution>
         <XStart>0</XStart>
         <YStart>0</YStart>
         <Width>1500</Width>
         <Height>2100</Height>
         <Format>Jpeg</Format>
         <CompressionQFactor>35</CompressionQFactor>
         <ColorSpace>Color</ColorSpace>
         <BitDepth>8</BitDepth>
         <InputSource>Platen</InputSource>
         <ContentType>Photo</ContentType>
       </ScanSettings>
       <ImageWidth>1000</ImageWidth>
       <ImageHeight>1400</ImageHeight>
       <BytesPerLine>3000</BytesPerLine>
       <Cooked>enabled</Cooked>
     </BufferInfo>
     <BinaryURL>/Scan/Jobs/39/Pages/1</BinaryURL>
     <ImageOrientation>Normal</ImageOrientation>
   </PreScanPage>
</ScanJob>
</j:Job>"""

txt2 = """<?xml version="1.0" encoding="UTF-8"?>
<!-- THIS DATA SUBJECT TO DISCLAIMER(S) INCLUDED WITH THE PRODUCT OF ORIGIN. -->
<j:Job xmlns:j="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30" xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" xmlns:fax="http://www.hp.com/schemas/imaging/con/fax/2008/06/13" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30 ../schemas/Jobs.xsd">
	<j:JobUrl>/Jobs/JobList/39</j:JobUrl>
	<j:JobCategory>Scan</j:JobCategory>
	<j:JobState>Completed</j:JobState>
	<j:JobStateUpdate>187-137</j:JobStateUpdate>
	<j:JobSource>userIO</j:JobSource>
	<ScanJob xmlns="http://www.hp.com/schemas/imaging/con/cnx/scan/2008/08/19">
   <PostScanPage>
     <PageNumber>1</PageNumber>
     <PageState>UploadCompleted</PageState>
     <TotalLines>1400</TotalLines>
   </PostScanPage>
</ScanJob>
</j:Job>"""

for t in [txt1, txt2]:
    xml_document = xml.dom.minidom.parseString(t)
    print(xml_document)
    jobState = xml_document.getElementsByTagName("j:JobState")[0].firstChild.data
    elem = None
    psp = xml_document.getElementsByTagName("PreScanPage")
    if psp:
        elem = psp[0]
    else:
        psp = xml_document.getElementsByTagName("PostScanPage")
        if psp:
            elem = psp[0]
    pageState = None
    if elem:
        pageState = elem.getElementsByTagName("PageState")[0].firstChild.data
    print(jobState, pageState)
