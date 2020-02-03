class LoggingCount():

    def assert_logging(self, count, logtype, caplog):
        """Check for expected number of errors in logging

        Parameters
        ----------
        count : int
            Number of errors expected
        caplog : caplog
            caplog object from original method call
        """
        c = 0
        for record in caplog.records:
            if record.levelname == logtype:
                c += 1
        assert c == count
