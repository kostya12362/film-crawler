import json

from base import BaseParserModel


class Item(BaseParserModel):
    id: str
    ratings_summary_aggregate: float
    ratings_summary_vote_count: int

    @property
    def _id(self):
        return self._response['id']

    @property
    def _ratings_summary_aggregate(self) -> float:
        return self._response['ratingsSummary']['aggregateRating']

    @property
    def _ratings_summary_vote_count(self) -> int:
        return self._response['ratingsSummary']['voteCount']


class SearchParser(BaseParserModel):

    def dict(self, *args, **kwargs) -> list[Item]:
        result = [
            Item(response=i['node']['title']) for i in
            json.loads(self._response.text)['data']['advancedTitleSearch']['edges']
        ]
        return result

    def after(self):
        return json.loads(self._response.text)['data']['advancedTitleSearch']['pageInfo']['endCursor']
