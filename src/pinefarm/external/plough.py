from . import interface
from .. import table
import requests
import shutil
import tarfile
import subprocess
import os
import pineappl

'''
Download grids + convert them to pineappl format
'''

class Plough(interface.External):

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)
        self.ps_link = self.source/"ploughshare_link.txt"
        self.link = self.ps_link.read_text()
        
        self.filename = self.link.rsplit('/')[-1]
        self.foldername = self.filename.rsplit('.', 1)[0]
        self.tarball = self.dest/self.filename
        self.processor = self.source/"process_grids.sh"
        self.run()
        self.generate_pineappl()
        self.timestamp = 0
    
    def run(self):
        '''
        Download and extract the .tgz file
        '''
        print("Downloading from ploughshare...")
        self.download_to_dest()
        print(f"Grids successfully downloaded to {self.tarball}")
        print("Extracting files...")
        self.extract_tarball()
        print(f"Grids successfully extracted to {self.foldername}")

    def results(self):
        pass

    def collect_versions(self):
        return {}
    
    def generate_pineappl(self):
        print("Grid conversion started...")
        # the grids are converted and processed here
        os.environ["PS_DIR"] = str(self.gridsfolder)
        # note that filename is also foldername
        os.environ["FILENAME"] = str(self.foldername)
        if os.access(self.processor, os.X_OK):
            shutil.copy2(self.processor, self.dest)
            subprocess.run("./process_grids.sh", cwd=self.dest, check=True)
            (self.dest/"process_grids.sh").unlink()
        else:
            raise ValueError(f"Grid conversion file present but not executable: {self.processor}")
        self.grids = []
        for g in self.dest.glob("*.pineappl.lz4"):
            self.grids.append(g)
        
    def download_to_dest(self):
        '''
        Download the file and move it to the output folder
        '''
        with requests.get(self.link, stream=True) as r:
            r.raise_for_status()
            with (self.dest/self.filename).open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

    def extract_tarball(self):
        '''
        extract the contents
        '''
        with tarfile.open(self.tarball, "r:*") as tf:
            tf.extractall(self.dest)
        self.gridsfolder = self.dest/self.foldername/"grids"