import logging
import subprocess
import os
import pathlib
import psutil


class PyEncfs():
    """Create, Mount and Unmount Encfs file systems

    python interface for inline encfs usage to work with encfs file systems
    using system.run shell excecution.
    """

    def __init__(self):
        self.name = "Encfs"
        self.log = logging.getLogger(__name__ + "." + self.name)
        self.log.debug("Initializing encfs")
        cmdok = True
        for c in ["echo", "encfs", "encfsctl", "fusermount"]:
            cmdok = cmdok and self._check_command(c)
        if not cmdok:
            self.log.critical("Not all required commands are available on "
                              "this system! encfs might not operate!")

    def _check_command(self, cmd):
        """Check if the given command exists using 'which'
        Parameters:
        ===========
        cmd : str
            shell command to locate using which

        Returns:
        ========
        True if which returns true
        """
        try:
            ret = subprocess.run("which " + str(cmd),
                                 shell=True, capture_output=True)
        except Exception:
            self.log.critical("Something wrong running which")
            self.log.exception("")
            return False
        if ret.returncode == 0:
            self.log.debug("found command %s at %s", cmd, ret.stdout)
            try:
                ret = subprocess.run(str(cmd) + " --version",
                                     shell=True, capture_output=True)
            except Exception:
                self.log.critical("Something wrong running "
                                  "%s --version", cmd)
                self.log.exception("")
                return False
            if ret.returncode == 0:
                self.log.debug("Version of %s - %s - %s",
                               cmd, ret.stdout, ret.stderr)
                return True
            else:
                return False
        else:
            self.log.error("Did not find command %s.", cmd)
            return False

    def _isencfsmount(self, path):
        """Check if a given mount point is an encfs mount point

        Parameters:
        ===========
        path : str
            path of the mount point

        Returns:
        ========
        True if path is an encfs mount point
        """
        if os.path.ismount(str(path)):
            for part in psutil.disk_partitions(True):
                if str(path) == str(part.mountpoint):
                    self.log.debug(
                            "Identified mountpoint: "
                            "mountpoint=%s; "
                            "fstype=%s;"
                            "device=%s;", part.mountpoint, part.fstype, part.device)
                    if str(part.device) == "encfs" and \
                            str(part.fstype) == "fuse.encfs":
                        return True
                    else:
                        self.log.warning("%s is not of type encfs!", path)
                        return False
        else:
            self.log.error("Given path is no mount point! %s", path)
            return False
        self.log.error("Error identifying mount point!")
        return False

    def _createpath(self, path):
        """Create given directory path

        Creates the given directory path. If path exists, the method checks
        if the path would be a valid mount point (empty directory and not
        used as a mount point, yet)

        Parameters:
        ===========
        path : str
            Path to create or check

        Returns:
        ========
        True if path is a valid potential mount point, False if not
        """
        if os.path.exists(str(path)):
            if os.path.isdir(str(path)):
                if os.listdir(str(path)) == []:
                    self.log.debug("Using existing empty directory instead"
                                   "! %s", path)
                    if os.path.ismount(str(path)):
                        self.log.error("Path is a mount point "
                                       "in use! %s", path)
                        return False
                    return True
                else:
                    self.log.error("Given path is not empty and cannot be "
                                   "used! %s", path)
                    return False
            else:
                self.log.error("Failed to create new directory! "
                               "%s exists and is not a directory!", path)
                return False
        else:
            try:
                pathlib.Path(str(path)).mkdir(parents=True, exist_ok=True)
            except Exception:
                self.log.exception("Failed to create path %s!",
                                   path)
                return False
        return True

    def create(self, path_encrypted, path_decrypted, password):
        """Create an encrypted encfs directory

        Create the encrypted directory and the decryption mount point
        (both must not exist before) and create encfs file system in the
        encrypted directory and mount to decryption mount point.

        Parameters:
        -----------
        path_encrypted : str
            path to the encrypted directory holding the encfs file system
            must not exist or must be empty!
        path_decrypted : str
            path to the decryption mount point to mount encrpyted directory to
            must not exist or must be empty!
        password : str
            Password to encrypt / decrypt files within encfs

        Returns:
        --------
        True on success and False on failure
        """
        if self._createpath(path_encrypted) and \
                self._createpath(path_decrypted):
            return self.mount(path_encrypted, path_decrypted, password)
        else:
            self.log.error("Failed to create new Encfs file system / "
                           "directory!")
            return False

    def mount(self, path_encrypted, path_decrypted, password):
        """Try to mount a given path as encfs file system.

        This method tries to run a shell command to mount a given path
        as an encfs file system. There is no reliable feedback, that the
        command worked successfully!

        Parameters:
        -----------
        path_encrypted : str
            path to the encrypted directory holding the encfs file system
            must not exist or must be empty!
        path_decrypted : str
            path to the decryption mount point to mount encrpyted directory to
            must not exist or must be empty!
        password : str
            Password to encrypt / decrypt files within encfs

        Returns:
        --------
        True on success and False on failure
        """

        if self._createpath(path_decrypted) and \
                os.path.isdir(str(path_encrypted)):
            try:
                subprocess.run("echo '" + str(password) + "' | " +
                               "encfs --standard --stdinpass '" +
                               str(path_encrypted) + "' '" +
                               str(path_decrypted) + "'", shell=True)
            except Exception:
                self.log.exception("Non-zero return value from encfs mount "
                                   "cmd")
                return False
            if os.path.ismount(str(path_decrypted)) and \
                    self._isencfsmount(path_decrypted):
                self.log.info("Encfs successfully mounted from "
                              "%s to %s!", path_encrypted, path_decrypted)
                return True
            else:
                self.log.error("Failed to detect valid mount point at "
                               "path_decrypted! %s", path_decrypted)
                return False
        else:
            self.log.error("Failed to mount encfs file system!")
            return False

    def umount(self, path):
        """Unmount file system using "fusermount -u <path>"

        Check if given path is a valid mount point, try to unmount and
        check for success

        Parameters:
        ===========
        path : str
            path to unmount

        Returns:
        ========
        True on success and False on failure
        """
        if not os.path.ismount(str(path)):
            self.log.warning("Given path is not a mount point! "
                             "Nothing to unmount at %s.", path)
            return False
        if not self._isencfsmount(path):
            self.log.warning("Refusing to unmount none encfs fstype!")
            return False

        try:
            ret = subprocess.run("fusermount -u '" + str(path) + "'",
                                 shell=True)
        except Exception:
            self.log.exception("Non-zero return value from passwd "
                               "check command")
            return False
        if os.path.ismount(str(path)) or ret.returncode != 0:
            self.log.error("Failed to unmount path! %s", path)
            return False
        else:
            return True

    def change_password(self, path_encrypted, password_current, password_new):
        """Change the password for the encfs file system to a new password

        Parameters:
        ===========
        path_encrypted : str
            path to the encrypted directory holding the encfs file system
        password_current: str
            current password of the encfs file system
        password_new: str
            new password of the encfs file system

        Returns:
        ========
        True on success and False on failure
        """
        ret = None
        try:
            ret = subprocess.run("echo '" + str(password_current) +
                                 "\n" + str(password_new) + "' | " +
                                 "encfsctl autopasswd '" +
                                 str(path_encrypted) + "'",
                                 shell=True, capture_output=True)
        except Exception:
            self.log.exception("Non-zero return value from passwd "
                               "check command")
            return False

        if b'Volume Key successfully updated' not in ret.stdout and \
                ret.returncode == 1:
            self.log.error("Failed to change password!")
            return False

        if self.check_password(path_encrypted, password_new):
            self.log.debug("Password successfully changed!")
            return True
        else:
            self.log.error("Unexpected happened")
            return False

    def check_password(self, path_encrypted, password):
        """Change the password for the encfs file system to a new password

        Parameters:
        ===========
        password: str
            current password of the encfs file system
        path_encrypted : str
            path to the encrypted directory holding the encfs file system

        Returns:
        ========
        True on success and False on failure
        """
        ret = None
        try:
            ret = subprocess.run("echo '" + str(password) + "' | " +
                                 "encfsctl autocheckpasswd '" +
                                 str(path_encrypted) + "'",
                                 shell=True, capture_output=True)
        except Exception:
            self.log.exception("Non-zero return value from passwd"
                               " check command")
            return False

        if b'Invalid password' in ret.stdout and ret.returncode == 1:
            self.log.error("Not the correct password!")
            return False
        elif b'Password is correct' in ret.stdout and ret.returncode == 0:
            self.log.debug("Password is correct!")
            return True
        else:
            return False

    def is_encfs(self, path_encrypted):
        """Check if the given path is a valid encfs directory

        Parameters:
        ===========
        path_encrypted : str
            path to the encrypted directory holding the encfs file system

        Returns:
        ========
        True on success and False on failure
        """
        ret = None
        try:
            ret = subprocess.run("encfsctl '" +
                                 str(path_encrypted) + "'",
                                 shell=True, capture_output=True)
        except Exception:
            self.log.exception("Non-zero return value from passwd"
                               " check command")
            return False

        if b'Unable to load or parse config file' in ret.stdout or \
                ret.returncode == 1:
            self.log.debug("Path is not a valid encfs directory")
            return False
        elif b'Key Size:' in ret.stdout and ret.returncode == 0:
            self.log.debug("Path is a valid encfs directory")
            return True
        else:
            return False
