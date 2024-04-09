import os
import shutil
import subprocess
import traceback
from http.client import HTTPConnection


class CompileTest:
    def __init__(self):
        self.success = False
        self.status = ""

    def run(self):
        try:
            os.remove('../submission/server')
        except OSError:
            pass

        try:
            subprocess.run(['make', '-C', '../submission'],
                           capture_output=True, check=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            self.status = 'Compilation timeout'
            return
        except subprocess.CalledProcessError as err:
            self.status = 'Compilation Error: ' + err.stderr
            return

        try:
            shutil.copy('../submission/server', 'server')
        except Exception:
            self.status = 'Cannot find executable called "server" under root directory'
            return

        self.success = True

    def get_result(self):
        result_dict = {
            'status': 'passed' if self.success else 'failed',
            'name': 'Compilation',
            'output': self.status,
            'visibility': 'visible'
        }
        return [result_dict]


class RequestTest:
    def __init__(self, name, url, filename, status_pts=-1, visibility='visible'):  # visibility=after_published
        self.name = name
        self.url = url
        self.filename = filename
        self.status_pts = 0
        self.status_output = 'Failed'
        self.status_full_pts = status_pts
        self.visibility = visibility

    def run(self, host, port):
        try:
            conn = HTTPConnection(host, port, timeout=5)
            conn.request('GET', self.url)
            r1 = conn.getresponse()
            if r1.version in [10, 11] and r1.status == 200 and r1.reason == 'OK':
                self.status_pts = self.status_full_pts
                self.status_output = 'Success'
            else:
                self.status_output = 'Malformed HTTP response (version/status code)'
        except TimeoutError:
            self.status_output = 'Timeout getting HTTP response'
            return
        except Exception:
            self.status_output = 'Error when getting HTTP response'
            traceback.print_exc()
            return

    def get_result(self):
        result_list = []
        if self.status_full_pts > 0:
            status_result = {
                'score': self.status_pts,
                'max_score': self.status_full_pts,
                'name': self.name + ': HTTP response header',
                'status': 'passed' if self.status_pts == self.status_full_pts else 'failed',
                'output': self.status_output,
                'visibility': self.visibility
            }
            result_list.append(status_result)
        return result_list