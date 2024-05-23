from api_scrapy.api import ScrapyAPI

app = ScrapyAPI(
    title='JustwatchCrawler',
    # secret_key='test',
    version='0.1',
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run('main:app', port=5044, reload=True)
