#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
仮想のテキストファイルを表示させるFUSE App
"""


from __future__ import with_statement

import os
import sys
import logging
import errno

from fuse import FUSE, FuseOSError, Operations

class VirtualFileDiscripter(Operations):
    # 仮想ファイル名
    VIRTUAL_FILE = u'nothing.txt'
    VIRTUAL_FILE_VALUE = 'ほげほげほげ'*10000+'end\n'

    def __init__(self, root):
        self.root = root
        logging.debug('virtual file name:%s'  , self.VIRTUAL_FILE)
        logging.debug('virtual file value:%s' , self.VIRTUAL_FILE_VALUE)

    # Helpers
    # =======

    def _full_path(self, partial):
        logging.debug('call _full_path [partial:%s]', partial)
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        logging.debug('call access [path:%s, mode:%s]', path, mode)
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        logging.debug('call chmod [path:%s]', path)
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        logging.debug('call chown [path:%s]', path)
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        if path == u'/' + self.VIRTUAL_FILE:
            attr={'st_ctime': 0, 'st_mtime': 0, 'st_nlink': 1, 'st_mode': 33060, 'st_size': len(self.VIRTUAL_FILE_VALUE), 'st_gid': 1004, 'st_uid': 1000, 'st_atime': 0}
        else:
            full_path = self._full_path(path)
            st = os.lstat(full_path)
            attr = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                    'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        logging.debug('call getattr [path:%s, attr:%s]', path, attr)
        return attr
    
    def readdir(self, path, fh):
        """
        ディレクトリリスティング用のメソッド
        """
        logging.debug('call readdir [path:%s]', path)
        dirents = [u'.', u'..', self.VIRTUAL_FILE]
        
        full_path = self._full_path(path)
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        logging.debug('call readlink [path:%s]', path)
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        logging.debug('call mknod [path:%s]', path)
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        logging.debug('call rmdir [path:%s]', path)
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        logging.debug('call mkdir [path:%s]', path)
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        logging.debug('call statfs [path:%s]', path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        logging.debug('call ulink [path:%s]', path)
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        logging.debug('call symlink [path:%s]', path)
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        logging.debug('call rename [path:%s]', path)
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        logging.debug('call link [path:%s]', path)
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        logging.debug('call utimens [path:%s]', path)
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        """
        ファイルオープン
        """
        if path == u'/' + self.VIRTUAL_FILE:
            # ファイルディスクリプタを返す（任意の整数を返すことにする）
            fd = 55110
        else:
            full_path = self._full_path(path)
            fd = os.open(full_path, flags)
        logging.debug('call open [path:%s, flags:%s, fd:%d]', path, flags, fd)
        return fd

    def create(self, path, mode, fi=None):
        logging.debug('call create [path:%s]', path)
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, size, offset, fh):
        """
        ファイルを読み込むメソッド
        """
        logging.debug('call read [path:%s, size:%d, offset:%d, fh:%d]', path, size, offset, fh)
        if path == u'/' + self.VIRTUAL_FILE:
            return self.VIRTUAL_FILE_VALUE[offset:offset+size]
        else:
            os.lseek(fh, offset, os.SEEK_SET)
            return os.read(fh, size)

    def write(self, path, buf, offset, fh):
        logging.debug('call write [path:%s]', path)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        logging.debug('call truncate [path:%s]', path)
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        logging.debug('call flush [path:%s]', path)
        if path == u'/' + self.VIRTUAL_FILE:
            return None
        else:
            return os.fsync(fh)

    def release(self, path, fh):
        logging.debug('release call [path:%s]', path)
        if path == u'/' + self.VIRTUAL_FILE:
            return None
        else:
            return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        logging.debug('fsync call', path)
        return self.flush(path, fh)


def main(mountpoint, root):
    logging.info('runining main')
    FUSE(VirtualFileDiscripter(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    # log config
    logging.basicConfig(format='%(asctime)s: %(message)s',level=logging.DEBUG)
    main(sys.argv[2], sys.argv[1])

