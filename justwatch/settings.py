import os
import warnings
import aioscrapy.exceptions
warnings.filterwarnings("ignore", category=aioscrapy.exceptions.ScrapyDeprecationWarning)

BOT_NAME = 'justwatch'

SPIDER_MODULES = ['justwatch.spiders']
NEWSPIDER_MODULE = 'justwatch.spiders'

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/" \
             "537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36"

URLLENGTH_LIMIT = 5000

ROBOTSTXT_OBEY = False

DEBUG = False if os.getenv('DEBUG') == 'False' else True
DEBUG_DELTA_DAYS = 50

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 502,
    # 'scrapy.downloadermiddlewares.retry.DownloaderMiddlewareManager': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'justwatch.middlewares.TooManyRequestsRetryMiddleware': 500,
}

SCRAPYD_HOST = os.getenv('SCRAPYD_HOST', 'localhost')
SCRAPYD_USERNAME = os.getenv('SCRAPYD_USERNAME')
SCRAPYD_PASSWORD = os.getenv('SCRAPYD_PASSWORD')

SCRAPY_PROXY_USERNAME = os.getenv('SCRAPY_PROXY_USERNAME')
SCRAPY_PROXY_PASSWORD = os.getenv('SCRAPY_PROXY_PASSWORD')
SCRAPY_PROXY_PORT = os.getenv('SCRAPY_PROXY_PORT')


REDIS_DB = os.getenv('REDIS_DB', 1)
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_USER = os.getenv('MONGO_INITDB_ROOT_USERNAME')

MONGO_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
MONGO_PORT = os.getenv('MONGO_PORT')

MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
SECRET_KEY = os.getenv('SECRET_KEY')
