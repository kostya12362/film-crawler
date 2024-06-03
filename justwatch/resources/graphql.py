import json
from .сonstants import *


class QueryControl:

    # region OldMethods
    @staticmethod
    def _interpolate_parameters(query_string, **parameters):
        for key, value in parameters.items():
            query_string = query_string.replace(f'${key}', f'"{value}"')
        return query_string

    @staticmethod
    def fragment_suggested(language: str, country: str):
        fragment_suggested = f"""
        fragment SuggestedOffer on Offer {{
            id
            presentationType
            monetizationType
            retailPrice(language: $language)
            retailPriceValue
            currency
            lastChangeRetailPriceValue
            type
            package {{
                id
                packageId
                clearName
                __typename
            }}
            standardWebURL
            elementCount
            availableTo
            deeplinkRoku: deeplinkURL(platform: ROKU_OS)
            __typename
        }}

        fragment SuggestedTitle on MovieOrShow {{
            id
            objectType
            objectId
            content(country: $country, language: $language) {{
                fullPath
                title
                externalIds {{
                    imdbId
                    __typename
                }}
                originalReleaseYear
                posterUrl
                fullPath
                __typename
            }}
            offers(country: $country, platform: WEB) {{
                ...SuggestedOffer
                __typename
            }}
            __typename
        }}
        """
        return QueryControl._interpolate_parameters(fragment_suggested, language=language, country=country)

    def query_movie_by_id(self, country: str, language: str, node_id: str):
        query_movie_by_id = f'''
        query GetSuggestedTitles(
        $country: Country!, $language: Language!, $nodeId: ID!) {{
            node(id: $nodeId) {{
                ...SuggestedTitle
            }}
        }}
        ''' + self.fragment_suggested(language, country)

        return QueryControl._interpolate_parameters(query_movie_by_id, country=country,
                                                    language=language, nodeId=node_id)

    # endregion

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
    def get_search_film(i):
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

    # get_all_Localization method
    #
    # def get_all_films(self, countries):
    #     return json.dumps({
    #         "query": self.create_query(countries),
    #         "variables": self.get_variables,
    #     })
    #
    # def get_variables(self, countries: list[dict[str, str]], justwatch_id: str):
    #     variables = dict()
    #     for i, v in enumerate(countries):
    #         variables |= {f"country_{i}": v['country'], f"language_{i}": v['language']}
    #     variables['nodeId'] = justwatch_id
    #     return variables
