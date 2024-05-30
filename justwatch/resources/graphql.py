class QueryControl:
    def __init__(self):
        pass

    def get_all_packages(self, icon_format, icon_profile, platform, packages_country, monetization_types):
        return f'''
        query GetPackagesByMonetizationType(
            $iconFormat: ImageFormat! = {icon_format},
            $iconProfile: IconProfile! = {icon_profile},
            $platform: Platform! = {platform},
            $packagesCountry: Country! = {packages_country},
            $monetizationTypes: [MonetizationType!] = {monetization_types}
        ) {{
            packages(
                country: $packagesCountry, platform: $platform, monetizationTypes: $monetizationTypes, includeAddons: true
            ) {{
                ...PackageEntityFields
                bundles(platform: $platform, country: $packagesCountry) {{
                    ...BundleFields
                    packages(country: $packagesCountry, platform: $platform) {{
                        ...PackageEntityFields
                        __typename
                    }}
                    __typename
                }}
                addons(country: $packagesCountry, platform: $platform) {{
                    ...PackageEntityFields
                    __typename
                }}
                __typename
            }}
            trackingPackages: packages(
                country: $packagesCountry,
                platform: $platform,
                monetizationTypes: $monetizationTypes,
                includeAddons: true
            ) {{
                ...PackageEntityFields
                bundles(platform: $platform, country: $packagesCountry) {{
                    ...BundleFields
                    packages(country: $packagesCountry, platform: $platform) {{
                        ...PackageEntityFields
                        __typename
                    }}
                    __typename
                }}
                __typename
            }}
        }}

        fragment PackageEntityFields on Package {{
            clearName
            id
            shortName
            technicalName
            icon
            packageId
            selected
            addonParent(country: $packagesCountry, platform: $platform) {{
                technicalName
                packageId
                shortName
                __typename
            }}
            __typename
        }}

        fragment BundleFields on Bundle {{
            clearName
            icon(format: $iconFormat, profile: $iconProfile)
            id
            shortName
            technicalName
            bundleId
            selected
            __typename
        }}
        '''

    def get_suggested_titles(self, country, language, first, filter):
        fragment_suggested = '''
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
        '''

        query_search_pages = f'''
        query GetSuggestedTitles($country: Country!, $language: Language!, $first: Int!, $filter: TitleFilter) {{
            popularTitles(country: $country, first: $first, filter: $filter) {{
                edges {{
                    node {{
                        ...SuggestedTitle
                        __typename
                    }}
                    __typename
                }}
                __typename
            }}
        }}
        ''' + fragment_suggested

        return query_search_pages

    def get_movie_by_id(self, country, language, node_id):
        fragment_suggested = '''
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
        '''

        query_get_movie_by_id = f'''
        query GetSuggestedTitles($country: Country!, $language: Language!, $nodeId: ID!) {{
            node(id: $nodeId) {{
                ...SuggestedTitle
            }}
        }}
        ''' + fragment_suggested

        return query_get_movie_by_id


qc = QueryControl()

query_all_packages = qc.get_all_packages("WEBP", "S100", "WEB", "US", [])
print("Query Get All Packages:\n", query_all_packages)

query_suggested_titles = qc.get_suggested_titles("US", "EN", 10, "")
print("Query Get Suggested Titles:\n", query_suggested_titles)

query_movie_by_id = qc.get_movie_by_id("US", "EN", "12345")
print("Query Get Movie By ID:\n", query_movie_by_id)
