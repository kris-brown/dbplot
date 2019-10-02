# External Modules
from typing  import List, Any
from time    import sleep
from os      import environ
from os.path import exists
from random  import random
from pprint  import pformat
from json    import load, dump

from psycopg2        import connect,Error                   # type: ignore
from psycopg2.extras import DictCursor                      # type: ignore
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # type: ignore

Connection = Any

################################################################################

class ConnectInfo(object):
    """
    PostGreSQL connection info
    """
    def __init__(self,
                 host   : str = '127.0.0.1',
                 port   : int = 5432,
                 user   : str = None,
                 passwd : str = None,
                 db     : str = ''
                ) -> None:

        if not user:
            user = passwd = environ["USER"]

        self.host   = host
        self.port   = port
        self.user   = user
        self.passwd = passwd
        self.db     = db

    def __str__(self) -> str:
        return pformat(self.__dict__)

    def connect(self, attempt : int  = 3) -> Connection:
        e = ''
        for _ in range(attempt):
            try:
                conn = connect(host        = self.host,
                               port        = self.port,
                               user        = self.user,
                               password    = self.passwd,
                               dbname      = self.db,
                               connect_timeout = 28800)
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                return conn
            except Error as e:
                print(e); sleep(1)

        raise Error()

    def to_file(self, pth : str) -> None:
        '''Store connectinfo data as a JSON file'''
        with open(pth,'w') as f:
            dump(vars(self),f)

    @staticmethod
    def from_file(pth : str) -> 'ConnectInfo':
        """
        Create from path to file with ConnectInfo fields in JSON format
        """
        assert exists(pth), 'Error loading connection info: no file at '+pth
        with open(pth,'r') as f:
            return ConnectInfo(**load(f))

    def select_dict(self, q : str, binds : list = []) -> List[dict]:
        # print('SELECTING with: \n'+sub(q,binds))
        with self.connect().cursor(cursor_factory=DictCursor) as cxn:
            cxn.execute(q.replace('%','%%'),vars=binds)
            return cxn.fetchall()
