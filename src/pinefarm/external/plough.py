"""Download grids + convert them to pineappl format."""

import os
import shutil
import subprocess
import tarfile
import urllib.request

import pineappl
import requests

from .. import table
from . import interface

PLOUGHSHARE_LINK_FILENAME = "ploughshare_link.txt"
GRIDS_PROCESSOR = "process_grids.sh"
GRIDS_TMP = "grids"


class Plough(interface.External):
    """Interface provider."""

    def __init__(self, pinecard, theorycard, *args, **kwargs):
        super().__init__(pinecard, theorycard, *args, **kwargs)
        self.ps_link = self.source / PLOUGHSHARE_LINK_FILENAME
        self.link = self.ps_link.read_text()

        self.filename = self.link.rsplit("/")[-1]
        self.dir_name = self.filename.rsplit(".", 1)[0]
        self.tarball = self.dest / self.filename
        self.processor = self.source / GRIDS_PROCESSOR
        self.run()
        self.generate_pineappl()
        self.timestamp = 0

    def run(self):
        """Download and extract the .tgz file."""
        print("Downloading from ploughshare...")
        self.download_to_dest()
        print(f"Grids successfully downloaded to {self.tarball}")
        print("Extracting files...")
        self.extract_tarball()
        print(f"Grids successfully extracted to {self.dir_name}")

    def results(self):
        """Results are collected and compared at the pineappl (script) level."""
        pass

    def collect_versions(self):
        """No additional programs involved."""
        return {}

    def generate_pineappl(self):
        """Converts donwloaded grids into pineappl format."""
        print("Grid conversion started...")
        # the grids are converted and processed here
        os.environ["PS_DIR"] = str(self.grids_dir)
        # note that filename is also dir_name
        os.environ["FILENAME"] = str(self.dir_name)
        if os.access(self.processor, os.X_OK):
            shutil.copy2(self.processor, self.dest)
            subprocess.run("./process_grids.sh", cwd=self.dest, check=True)
            (self.dest / "process_grids.sh").unlink()
        else:
            raise ValueError(
                f"Grid conversion file present but not executable: {self.processor}"
            )
        self.grids = []
        for g in self.dest.glob("*.pineappl.lz4"):
            self.grids.append(g)

    def download_to_dest(self):
        """Download the file and move it to the output folder."""
        urllib.request.urlretrieve(self.link, self.dest / self.filename)

    def extract_tarball(self):
        """Extract the contents."""
        with tarfile.open(self.tarball, "r:*") as tf:
            tf.extractall(self.dest)
        self.grids_dir = self.dest / self.dir_name / GRIDS_TMP
