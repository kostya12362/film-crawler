class QueryControl:
    pass

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

    @staticmethod
    def query_all_packages(icon_format, icon_profile, platform, packages_country, monetization_types):
        query_all_packages = f"""
        query GetPackagesByMonetizationType(
            $iconFormat: ImageFormat! = {icon_format},
            $iconProfile: IconProfile! = {icon_profile},
            $platform: Platform! = {platform},
            $packagesCountry: Country! = {packages_country},
            $monetizationTypes: [MonetizationType!] = {monetization_types}
        ) {{
            packages(
                country: $packagesCountry, platform: $platform, 
                monetizationTypes: $monetizationTypes, includeAddons: true
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
        """
        return QueryControl._interpolate_parameters(query_all_packages, iconFormat=icon_format,
                                                    iconProfile=icon_profile, platform=platform,
                                                    packagesCountry=packages_country,
                                                    monetizationTypes=monetization_types)

    def query_search_pages(self, country: str, language: str, first, filter_param):
        self.fragment_suggested(language, country)
        query_search_pages = f'''
                query GetSuggestedTitles(
                $country: Country!, $language: Language!, $first: Int!, $filter: TitleFilter) {{
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
                ''' + self.fragment_suggested(language, country)

        return QueryControl._interpolate_parameters(query_search_pages, country=country,
                                                    language=language, first=first, filter=filter_param)

    def query_movie_by_id(self, country: str, language: str, node_id: str):
        self.fragment_suggested(language, country)

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

    # VARIABLES_GET_ALL_PACKAGES = {
    #     "iconFormat": "WEBP",
    #     "iconProfile": "S100",
    #     "platform": "WEB",
    #     "packagesCountry": "US",
    #     "monetizationTypes": []
    # }

# qc = QueryControl()
#
# query_all_packages = qc.query_all_packages("WEBP", "S100", "WEB", "US", [])
# print("Query Get All Packages:\n", query_all_packages)
#
# query_search_pages = qc.query_search_pages("US", "EN", 10, "")
# print("Query Get Suggested Titles:\n", query_search_pages)
#
# query_movie_by_id = qc.get_movie_by_id("US", "EN", "12345")
# print("Query Get Movie By ID:\n", query_movie_by_id)
