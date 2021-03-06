# -*- coding: utf-8 -*-
# !/usr/bin/python3
"""
    API: A generic FTP wrapper for TPW Integration
    : copyright: (c) 2012 by emipro Technologies
    : license: AGPL3, see LICENSE for more details.
"""
import csv
import logging
from io import BytesIO
from ftplib import FTP
from tempfile import NamedTemporaryFile
import os
from datetime import datetime
import sys

_logger = logging.getLogger("FTP Connector EPT")


class UnicodeDictReader(csv.DictReader):
    def __init__(self, csvfile, *args, **kwargs):
        """
        Allows to specify an additional keyword argument encoding which defaults to "utf-8"
        """
        self.encoding = kwargs.pop('encoding', 'utf-8')
        csv.DictReader.__init__(self, csvfile, *args, **kwargs)

    def __next__(self):
        if sys.version_info[0] < 3:
            rv = csv.DictReader.__next__()(self)
            return dict((
                (k, v.decode(self.encoding, 'ignore') if v else v) for k, v in list(rv.items())
            ))
        elif sys.version_info[0] >= 3:
            rv = csv.DictReader.__next__(self)
            return dict((
                (k, v if v else v) for k, v in list(rv.items())
            ))


class UnicodeDictWriter(csv.DictWriter):
    def __init__(self, csvfile, fieldnames, *args, **kwargs):
        """
        Allows to specify an additional keyword argument encoding which defaults to "utf-8"
        """
        self.encoding = kwargs.pop('encoding', 'utf-8')
        csv.DictWriter.__init__(self, csvfile, fieldnames, *args, **kwargs)

    def _dict_to_list(self, rowdict):
        rv = csv.DictWriter._dict_to_list(self, rowdict)
        return [(f.encode(self.encoding, 'ignore') if isinstance(f, str) else f) \
                for f in rv]


class TPWFTPInterface(object):
    """
    A class to represent an FTP connection to the TPW FTP location. This is
    mostly written as an abstraction around :py:mod:`~ftplib`.

    :param host: Hostname of the TPW server
    :param user: Username for accessing the FTP share
    :param passwd: Password for the FTP share
    :param from_TPW_dir: Name of the direcory from which files need to be
                         imported
    :param to_TPW_dir: Name of the directory to which files need to be  uploaded
    """

    client = None

    def __init__(self, host, user, passwd, from_tpw_dir, to_tpw_dir, archive_dir='', port=21):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port
        self.client = FTP()
        self.client.connect(self.host, self.port)
        self.from_tpw_dir = from_tpw_dir
        self.to_tpw_dir = to_tpw_dir
        self.archive_dir = archive_dir

    def __enter__(self):
        self.client.login(self.user, self.passwd)
        return self

    def set_pasv(self, mode):
        self.client.set_pasv(mode)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.quit()
        self.client.close()

    def push_to_ftp(self, filename, file):
        """
        Uploads the given file in a binary transfer mode to the `to_TPW_dir`

        :param filename: filename of the created file
        :param file: An open file or a file like object
        """
        self.client.cwd(self.to_tpw_dir)
        new_file = BytesIO(file.read().encode())
        self.client.storbinary('STOR %s' % filename, new_file)

    def pull_from_ftp(self, pattern, latest=False):
        self.client.cwd(self.from_tpw_dir)
        matched_files = []
        for f in self.client.nlst():
            if f.strip().startswith(pattern):
                matched_files.append(f)

        matched_files.sort()
        files_to_export = []
        print("Files : ", matched_files)

        for file_to_import in matched_files:
            file = NamedTemporaryFile(delete=False)

            self.client.retrbinary('RETR %s' % file_to_import, file.write)
            file.close()

            files_to_export.append(file.name)

        print("file to export : ", files_to_export)
        return (files_to_export, matched_files)

    def delete_from_ftp(self, filenames):
        """
        Delete the files for the filenames provided from the FTP location
        """
        for filename in filenames:
            self.client.cwd(self.to_tpw_dir)
            self.client.delete(filename)
        return True

    def delete_from_tmp(self, filenames):
        """
        Delete the files for the filenames provided from the FTP location
        """
        for filename in filenames:
            os.remove(filename)
        return True

    def archive_file(self, filenames):
        """ Archive the files. """
        for filename in filenames:
            fromname = "%s/%s" % (self.from_tpw_dir, filename)
            date_time = datetime.now()
            filename = "%s_%s" % (filename[:-4], date_time.strftime('%Y_%m_%d_%H_%M_%S.csv'))
            toname = "%s/%s" % (self.archive_dir, filename)
            self.client.cwd(self.from_tpw_dir)
            try:
                self.client.rename(fromname, toname)
            except Exception as error:
                _logger.info("Getting Exception while archiving the file, "
                             "Exception: {}".format(error))
                pass
        return True
