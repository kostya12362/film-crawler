import json

from justwatch.resources.сonstants import QUERY_GET_ALL_PACKAGES, QUERY_SEARCH_PAGES, QUERY_GET_MOVIE_BY_ID


class QueryControl:
    @staticmethod
    def create_query(countries: list[dict[str, str]]) -> str:
        args = ','.join([f"$country_{i}: Country!, $language_{i}: Language!" for i in range(len(countries))])
        query = '\n'.join([f'''_{i}:node(id: $nodeId) {{
                    ...SuggestedTitle_{i} 
                }}''' for i in range(len(countries))])
        fragments = '\n'.join([f'''
                    fragment SuggestedOffer_{i} on Offer {{
                        monetizationType
                        presentationType
                        currency
                        retailPrice(language: $language_{i})
                        package {{
                            id
                        }}
                        standardWebURL
                     }}
                    fragment SuggestedTitle_{i} on MovieOrShow {{
                        id
                        offers(country: $country_{i}, platform: WEB) {{
                            ...SuggestedOffer_{i}
                            }}
                    }}''' for i in range(len(countries))])
        return f'''
                    query GetSuggestedTitles({args}, $nodeId: ID!) {{
                        {query}
                    }}
                    {fragments}
                '''

    @staticmethod
    def get_package_body(localization: str):
        return json.dumps({
            "query": QUERY_GET_ALL_PACKAGES,
            "variables": {
                "iconFormat": "WEBP",
                "iconProfile": "S100",
                "platform": "WEB",
                "packagesCountry": localization.split('_')[1],
                "monetizationTypes": []
            }
        })

    @staticmethod
    def search_film(i):
        return json.dumps({
            "query": QUERY_SEARCH_PAGES,
            "variables": {
                "country": "US",
                "language": "en",
                "first": 50,
                "filter_param": {
                    "searchQuery": i['titleName']
                },
            }
        })

    def get_all_localizations(self, countries, justwatch_id):
        return json.dumps({
            "query": self.create_query(countries),
            "variables": self.get_variables(countries, justwatch_id),
        })

    @staticmethod
    def get_variables(countries: list[dict[str, str]], justwatch_id: str):
        variables = dict()
        for i, v in enumerate(countries):
            variables |= {f"country_{i}": v['country'], f"language_{i}": v['language']}
        variables['nodeId'] = justwatch_id
        return variables
