"""fetch all the versions of Serv_U
according the snapshot of the 'http://www.serv-u.com/releasenotes', to fetch
all the versions of Serv_U

'http://www.serv-u.com/releasenotes' whois info: solarwinds

fetch versions count: 141
"""
import time
import random
import warnings
import requests
import functools
from lxml import etree
from loguru import logger
from typing import Optional


class Retry(object):
    """a retry class decorator
    requests retry_times 
    """

    def __init__(self, *, retry_times=3, min_secs=2, errors=(Exception, )):
        """
        :param retry_times: retry times
        :param min_secs: min_secs to call fn again
        :param errors: errors
        """
        self.retry_times: int = retry_times
        self.min_secs: int = min_secs
        self.errors: tuple = errors

    def __call__(self, fn: callable) -> callable:
        """
        :param fn: function to be decorated
        :return:
        """
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            for _ in range(self.retry_times):
                try:
                    return fn(*args, **kwargs)
                except self.errors as e:
                    logger.error(e)
                    time.sleep(self.min_secs * (1 + random.random()))

        return inner


class Spider(object):
    """serv-u spider
    """

    special_headers: dict = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/81.0.4044.129 Safari/537.36",
        "Referer": "https://web.archive.org/web/*/http://www.serv-u.com/releasenotes",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(self):
        self.headers: dict = Spider.special_headers
        self.fetch_url: dir = "https://web.archive.org/web/20170613210635/http://www.serv-u.com/releasenotes"

    @staticmethod
    def ignore_warnings():
        warnings.filterwarnings("ignore")

    @staticmethod
    def decode_page(pages_bytes: bytes, charsets: tuple = ("utf-8", )) -> Optional[str]:
        """
        :param pages_bytes: fetch url response content
        :param charsets: the charsets that use to decode
        :return:
        """
        page_html = None
        if pages_bytes is None:
            return page_html
        for charset in charsets:
            try:
                page_html = pages_bytes.decode(charset)
                break
            except UnicodeDecodeError:
                logger.error("content decode error by using {}!".format(charset))

        return page_html

    @Retry()
    def __send_request(self, url: str, *, charsets: tuple = ("utf-8", )) -> Optional[str]:
        """
        :param url: url
        :param charsets: the charsets that use to decode
        :return:
        """
        response = requests.get(url, headers=self.headers, verify=False)

        return Spider.decode_page(response.content, charsets) if response.status_code == 200 else None

    @staticmethod
    def __parse_data(html_str: Optional[str]) -> list:
        """
        get all the versions as a list from html_str
        :param html_str: fetch url response text
        :return:
        """
        version_list = []
        if html_str is None:
            return version_list
        element = etree.HTML(html_str)
        a_list = element.xpath("//div[@id='VersionContainer']/div")

        for a_label in a_list:
            specific_version_list = a_label.xpath("h3/text()")
            version_list.extend(
                [version.strip().split()[-1].lower() for version in specific_version_list]
            )

        return version_list

    @staticmethod
    def __save_data(versions: Optional[list]):
        """
        :param versions: versions to save
        :return:
        """
        print(versions)
        logger.info("versions count: {}".format(len(versions)))

        with open("serv_u_versions.txt", "w", encoding="utf-8") as f:
            f.writelines(version + "\n" for version in versions)

    def run(self):
        Spider.ignore_warnings()
        html_str = self.__send_request(self.fetch_url)
        version_list = self.__parse_data(html_str)
        self.__save_data(version_list)


if __name__ == '__main__':
    spider = Spider()
    spider.run()
