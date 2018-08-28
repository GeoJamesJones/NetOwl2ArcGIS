# NetOwl2ArcGIS
In order to run this demo, first download this GitHub repo.  

Inside of this repo, there are a few key files: 
	1. NetOwl2ArcGIS.py (script) - this script is the main script that will iterate over a folder, pass the documents to the NetOwl API, and then automatically add these features to an established feature service on ArcGIS Online or ArcGIS Enterprise. 

	2. DIFImageHosting.rdp - This is the Remote Desktop File that allows a user to connect to the Virtual Machine that is optimized to run the script.  The script as it currently is written is hard-coded to work off of this VM.  Please e-mail james_jones@esri.com for the password. 

Running the script:

	1.  Connect to the Virtual Machine via the included RDP file
	2. Navigate to C:\Users\dif_user\Documents\NetOwl2ArcGIS and ensure that the NetOwl2ArcGIS.py script is located there.  This directory is synced with the repo and will be updated if/when any changes are made to the master script. 
	3. Go to the Start Menu - Anaconda 3 - Anaconda Prompt
	4. Change the directory to the folder with the script in it.  (cd C:\Users\dif_user\Documents\NetOwl2ArcGIS)
	5. Initialize the python script (python NetOwl2ArcGIS.py)
