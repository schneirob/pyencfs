from tests.utils.logging import LoggingCount
from pyencfs import PyEncfs
import os
import mock
import logging


class TestPyEncfsIsPyEncfs(LoggingCount):

    def test_is_encfs(self, tmpdir):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e.is_encfs(tmpdir + "/e")
        assert e.umount(tmpdir + "/d")

    def test_is_not_encfs(self, tmpdir):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert not e.is_encfs(tmpdir + "/d")
        assert e.umount(tmpdir + "/d")

    def test_is_not_encfs_subprocess_failure(self, tmpdir):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        with mock.patch("subprocess.run",
                        side_effect=Exception("outch")):
            assert not e.is_encfs(tmpdir + "/e")
        assert e.umount(tmpdir + "/d")


class TestPyEncfsCheckCommand(LoggingCount):

    def test_check_command_which_failure(self):
        e = PyEncfs()
        with mock.patch("subprocess.run",
                        side_effect=Exception("outch")):
            assert not e._check_command("ls")

    def test_check_command_ls(self):
        e = PyEncfs()
        assert e._check_command("ls")

    def test_check_command_blablablub(self, caplog):
        e = PyEncfs()
        assert not e._check_command("blablablub123lkj")
        self.assert_logging(1, "ERROR", caplog)


class TestPyEncfsChangePassword(LoggingCount):

    def test_change_password_umount_subprocess_failure(self, tmpdir):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        with mock.patch("subprocess.run",
                        side_effect=Exception("outch")):
            assert not e.change_password(tmpdir + "/e", "PASSWORD", "PASSWD")
        assert e.umount(tmpdir + "/d")

    def test_change_password(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e.umount(tmpdir + "/d")
        assert e.change_password(tmpdir + "/e", "PASSWORD", "PASSWD")
        assert "Password successfully changed" in caplog.text

    def test_change_wrong_password(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e.umount(tmpdir + "/d")
        assert not e.change_password(tmpdir + "/e", "PASSWORD1", "PASSWD")
        assert "Failed to change password" in caplog.text


class TestPyEncfsCheckPassword(LoggingCount):

    def test_check_password_umount_subprocess_failure(self, tmpdir):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e.umount(tmpdir + "/d")
        with mock.patch("subprocess.run",
                        side_effect=Exception("outch")):
            assert not e.check_password(tmpdir + "/e", "PASSWORD")

    def test_check_correct_password(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e.umount(tmpdir + "/d")
        assert e.check_password(tmpdir + "/e", "PASSWORD")
        assert "Password is correct" in caplog.text

    def test_check_wrong_password(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e.umount(tmpdir + "/d")
        assert not e.check_password(tmpdir + "/e", "PASSWORD1")
        assert "Not the correct password" in caplog.text


class TestPyEncfsIsPyEncfsMount(LoggingCount):

    def test_path_is_encfs_mount(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e._isencfsmount(tmpdir + "/d")
        assert "Identified mountpoint" in caplog.text
        assert e.umount(tmpdir + "/d")

    def test_path_is_no_mountpoint(self, tmpdir, caplog):
        e = PyEncfs()
        assert not e._isencfsmount(tmpdir)
        assert "Given path is no mount point" in caplog.text

    def test_path_is_not_encfs(self, caplog):
        e = PyEncfs()
        assert not e._isencfsmount("/")
        assert "is not of type encfs" in caplog.text

    def test_error_reading_mount_points(self, tmpdir, caplog):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert e._isencfsmount(tmpdir + "/d")
        with mock.patch("psutil.disk_partitions",
                        mock.MagicMock(return_value={})):
            assert not e._isencfsmount(tmpdir + "/d")
        assert e.umount(tmpdir + "/d")
        assert "Error identifying mount point" in caplog.text


class TestPyEncfsUmount(LoggingCount):

    def test_encfs_umount_subprocess_failure(self, tmpdir):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        with mock.patch("subprocess.run",
                        side_effect=Exception("outch")):
            assert not e.umount(tmpdir + "/d")
        assert e.umount(tmpdir + "/d")

    def test_path_is_not_mounted(self, tmpdir, caplog):
        e = PyEncfs()
        assert not e.umount(tmpdir)
        assert "Given path is not a mount point!" in caplog.text

    def test_failed_umount(self, tmpdir, caplog):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        with mock.patch("subprocess.run", mock.MagicMock(return_value=True)):
            assert not e.umount(tmpdir + "/d")
        assert "Failed to unmount path!" in caplog.text
        assert e.umount(tmpdir + "/d")

    def test_non_encfs_file_system_type(self, caplog):
        e = PyEncfs()
        assert not e.umount("/")
        assert "Refusing to unmount none encfs" in caplog.text


class TestPyEncfsMount(LoggingCount):

    def test_encfs_mount_subprocess_failure(self, tmpdir):
        e = PyEncfs()
        assert e._createpath(tmpdir + "/e")
        assert e._createpath(tmpdir + "/d")
        with mock.patch("subprocess.run",
                        side_effect=Exception("outch")):
            assert not e.mount(tmpdir + "/e", tmpdir + "/d", "PASSWORD")

    def test_failed_subprocess_run(self, tmpdir, caplog):
        e = PyEncfs()
        assert e._createpath(tmpdir + "/e")
        assert e._createpath(tmpdir + "/d")
        with mock.patch("subprocess.run", mock.MagicMock(return_value=True)):
            assert not e.mount(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert "Failed to detect valid mount point at" in caplog.text

    def test_decryption_directory_is_file(self, tmpdir, caplog):
        e = PyEncfs()
        assert e._createpath(tmpdir + "/e")
        open(str(tmpdir + "/d"), "w+")
        assert not e.mount(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert "Failed to mount encfs file system" in caplog.text

    def test_encryption_directory_is_file(self, tmpdir, caplog):
        e = PyEncfs()
        assert e._createpath(tmpdir + "/d")
        open(str(tmpdir + "/e"), "w+")
        assert not e.mount(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert "Failed to mount encfs file system" in caplog.text


class TestPyEncfsCreate(LoggingCount):

    def test_successfull_creation(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert "Encfs successfully mounted" in caplog.text
        assert e.umount(tmpdir + "/d")

    def test_spaces_in_path_name(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e.create(tmpdir + "/e   ", tmpdir + "/d   ", "PASSWORD")
        assert os.path.isdir(str(tmpdir + "/e   "))
        assert os.path.isdir(str(tmpdir + "/d   "))
        assert "Encfs successfully mounted" in caplog.text
        assert os.path.ismount(str(tmpdir + "/d   "))
        assert e.umount(tmpdir + "/d   ")
        assert not os.path.ismount(str(tmpdir + "/d   "))

    def test_failure_with_invalid_directory(self, tmpdir, caplog):
        e = PyEncfs()
        open(str(tmpdir + "/foo.txt"), "w+")
        assert not e.create(tmpdir + "/foo.txt", tmpdir + "/d", "PASS")
        assert "Failed to create new Encfs file system" in caplog.text


class TestPyEncfsCreatePath(LoggingCount):

    def test_valid_multi_level_creation(self, tmpdir, caplog):
        e = PyEncfs()
        d = tmpdir + "/created_path/a/b/c/d/e/f/"
        assert e._createpath(d)
        assert os.path.isdir(str(d))
        self.assert_logging(0, "ERROR", caplog)
        assert "Using existing empty directory" not in caplog.text

    def test_spaces_in_file_names(self, tmpdir, caplog):
        e = PyEncfs()
        d = tmpdir + "/created path with spaces"
        assert e._createpath(d)
        assert os.path.isdir(str(d))
        self.assert_logging(0, "ERROR", caplog)
        assert "Using existing empty directory" not in caplog.text

    def test_empty_directory(self, tmpdir, caplog):
        caplog.set_level(logging.DEBUG)
        e = PyEncfs()
        assert e._createpath(tmpdir)
        self.assert_logging(0, "ERROR", caplog)
        assert "Using existing empty directory" in caplog.text

    def test_non_empty_directory(self, tmpdir, caplog):
        e = PyEncfs()
        open(str(tmpdir + "/foo.txt"), "w+")
        assert not e._createpath(tmpdir)
        self.assert_logging(1, "ERROR", caplog)
        assert "Given path is not empty" in caplog.text

    def test_path_is_file(self, tmpdir, caplog):
        e = PyEncfs()
        open(str(tmpdir + "/nodir"), "w+")
        assert not e._createpath(tmpdir + "/nodir")
        self.assert_logging(1, "ERROR", caplog)
        assert "is not a directory" in caplog.text

    def test_path_not_writeable(self, tmpdir, caplog):
        e = PyEncfs()
        assert e._createpath(tmpdir + "/userdir")
        os.chmod(str(tmpdir + "/userdir"), 0o000)
        assert not e._createpath(tmpdir + "/userdir/dir")
        self.assert_logging(1, "ERROR", caplog)
        assert "Failed to create path" in caplog.text

    def test_allready_mounted_directory(self, tmpdir, caplog):
        e = PyEncfs()
        assert e.create(tmpdir + "/e", tmpdir + "/d", "PASSWORD")
        assert not e._createpath(tmpdir + "/d")
        self.assert_logging(1, "ERROR", caplog)
        assert "Path is a mount point" in caplog.text
        assert e.umount(tmpdir + "/d")
