# QUERY_ALL_PAGES = '''
# query GetPopularTitles(
#     $country: Country!,
#     $popularTitlesFilter: TitleFilter,
#     $watchNowFilter: WatchNowOfferFilter!,
#     $popularAfterCursor: String,
#     $popularTitlesSortBy: PopularTitlesSorting! = POPULAR,
#     $first: Int! = 100, $language: Language!,
#     $platform: Platform! = WEB,
#     $sortRandomSeed: Int! = 0,
#     $profile: PosterProfile,
#     $backdropProfile: BackdropProfile, $format: ImageFormat) {
#         popularTitles(
#             country: $country
#             filter: $popularTitlesFilter
#             after: $popularAfterCursor
#             sortBy: $popularTitlesSortBy
#             first: $first
#             sortRandomSeed: $sortRandomSeed
#         ) {
#             totalCount
#             pageInfo {
#                 startCursor
#                 endCursor
#                 hasPreviousPage
#                 hasNextPage
#                 __typename
#             }
#             edges {
#                 ...PopularTitleGraphql
#                 __typename
#                 }
#             __typename
#             }
#         }
#
#         fragment PopularTitleGraphql on PopularTitlesEdge {
#             cursor
#             node {
#                 id
#                 objectId
#                 objectType
#                 content(country: $country, language: $language) {
#                     title
#                     fullPath
#                     externalIds {
#                         imdbId
#                     },
#                     scoring {
#                         imdbScore
#                     __typename
#                 }
#             posterUrl(profile: $profile, format: $format)
#             ... on ShowContent {
#                 backdrops(profile: $backdropProfile, format: $format) {
#                     backdropUrl
#                     __typename
#                     }
#                     __typename
#                 }
#                 isReleased
#                 __typename
#             }
#             likelistEntry {
#                 createdAt
#                 __typename
#             }
#             dislikelistEntry {
#                 createdAt
#                 __typename
#                 }
#             watchlistEntry {
#                 createdAt
#                 __typename
#                 }
#             watchNowOffer(country: $country, platform: $platform, filter: $watchNowFilter) {
#                 id
#                 standardWebURL
#                 package {
#                     id
#                     packageId
#                     slug
#
#                     clearName
#                     __typename
#                 }
#                 retailPrice(language: $language)
#                 retailPriceValue
#                 lastChangeRetailPriceValue
#                 currency
#                 presentationType
#                 monetizationType
#                 availableTo
#                 __typename
#             }
#             ... on Movie {
#                 seenlistEntry {
#                     createdAt
#                     __typename
#                 }
#                 __typename
#             }
#             ... on Show {
#                 seenState(country: $country) {
#                     seenEpisodeCount
#                     progress
#                     __typename
#                 }
#                 __typename
#             }
#             __typename
#         }
#         __typename
# }
# '''
#
# VARIABLES_ALL_PAGES = {
#     "popularTitlesSortBy": "POPULAR",
#     "first": 100,
#     "platform": "WEB",
#     "sortRandomSeed": 0,
#     "popularAfterCursor": "",
#     "popularTitlesFilter": {
#         "ageCertifications": [],
#         "excludeGenres": [],
#         "imdbScore": {"min": 0.0, "max": 10.0},
#
#         "excludeProductionCountries": [],
#         "genres": [],
#         "objectTypes": [],
#         "productionCountries": [],
#         "packages": [],
#         "excludeIrrelevantTitles": False,
#         "presentationTypes": [],
#         "monetizationTypes": []
#     },
#     "watchNowFilter": {
#         "packages": [],
#         "monetizationTypes": []
#     },
#     "language": "en",
#     "country": "US"
# }

# QUERY_GET_MOVIE = '''
# query GetTitleOffers(
#     $nodeId: ID!,
#     $country: Country!,
#     $language: Language!,
#     $filterFlatrate: OfferFilter!,
#     $filterBuy: OfferFilter!,
#     $filterRent: OfferFilter!,
#     $filterFree: OfferFilter!,
#     $platform: Platform! = WEB
#     ) {
#         node(id: $nodeId) {
#             id
#             __typename
#             ... on MovieOrShowOrSeasonOrEpisode {
#                 offerCount(country: $country, platform: $platform)
#                 flatrate: offers(country: $country platform: $platform filter: $filterFlatrate) {
#                         ...TitleOffer
#                         __typename
#                 }
#                 buy: offers(country: $country, platform: $platform, filter: $filterBuy) {
#                     ...TitleOffer
#                     __typename
#                 }
#                 rent: offers(country: $country, platform: $platform, filter: $filterRent) {
#                     ...TitleOffer
#                     __typename
#                 }
#                 free: offers(country: $country, platform: $platform, filter: $filterFree) {
#                     ...TitleOffer
#                     __typename
#                 }
#                 __typename
#             }
#         }
#     }
#
#
# fragment TitleOffer on Offer {
#     id
#     presentationType
#     monetizationType
#     retailPrice(language: $language)
#     retailPriceValue
#     currency
#     lastChangeRetailPriceValue
#     type
#     package {
#         id
#         packageId
#         clearName
#         __typename
#         }
#     standardWebURL
#     elementCount
#     availableTo
#     deeplinkRoku: deeplinkURL(platform: ROKU_OS)
#     __typename
# }
# '''

# VARIABLES_GET_MOVIES = {
#     'platform': 'WEB',
#     'nodeId': None,
#     'country': 'US',
#     'language': 'en',
#     'filterBuy': {
#         'monetizationTypes': ['BUY'],
#         'bestOnly': True
#     },
#     'filterFlatrate': {
#         'monetizationTypes': ['FLATRATE', 'FLATRATE_AND_BUY', 'ADS', 'FREE', 'CINEMA'],
#         'bestOnly': True
#     },
#     'filterRent': {
#         'monetizationTypes': ['RENT'],
#         'bestOnly': True
#     },
#     'filterFree': {
#         'monetizationTypes': ['ADS', 'FREE'],
#         'bestOnly': True
#     }
# }

QUERY_GET_ALL_PACKAGES = '''
query GetPackagesByMonetizationType(
    $iconFormat: ImageFormat! = WEBP,
    $iconProfile: IconProfile! = S100,
    $platform: Platform! = WEB,
    $packagesCountry: Country!,
    $monetizationTypes: [MonetizationType!]
    ) {
        packages(
            country: $packagesCountry platform: $platform monetizationTypes: $monetizationTypes includeAddons: true
            ) {
                ...PackageEntityFields
                bundles(platform: $platform, country: $packagesCountry) {
                    ...BundleFields
                    packages(country: $packagesCountry, platform: $platform) {
                        ...PackageEntityFields
                        __typename
                        }
                        __typename
                    }
                addons(country: $packagesCountry, platform: $platform) {
                    ...PackageEntityFields
                    __typename
                    }
                __typename
                }
                trackingPackages: packages(
                    country: $packagesCountry
                    platform: $platform
                    monetizationTypes: $monetizationTypes
                    includeAddons: true
                    ) {
                        ...PackageEntityFields
                        bundles(platform: $platform, country: $packagesCountry) {
                            ...BundleFields
                            packages(country: $packagesCountry, platform: $platform) {
                                ...PackageEntityFields
                                __typename
                                }
                            __typename
                        }
                    __typename
                    }
                }

                fragment PackageEntityFields on Package {
                    clearName
                    id
                    shortName
                    technicalName
                    icon
                    packageId
                    selected
                    addonParent(country: $packagesCountry, platform: $platform) {
                        technicalName
                        packageId
                        shortName
                        __typename
                    }
                    __typename
                }

                fragment BundleFields on Bundle {
                    clearName
                    icon(format: $iconFormat, profile: $iconProfile)
                    id
                    shortName
                    technicalName
                    bundleId
                    selected
                    __typename
                }

'''

FRAGMENT_SUGGESTED = '''
fragment SuggestedOffer on Offer {
    id
    presentationType
    monetizationType
    retailPrice(language: $language)
    retailPriceValue
    currency
    lastChangeRetailPriceValue
    type
    package {
        id
        packageId
        clearName
        __typename
        }
    standardWebURL
    elementCount
    availableTo
    deeplinkRoku: deeplinkURL(platform: ROKU_OS)
    __typename
}

fragment SuggestedTitle on MovieOrShow {
  id
  objectType
  objectId
  content(country: $country, language: $language) {
    fullPath
    title
    externalIds {
        imdbId
        __typename
    }
    originalReleaseYear
    posterUrl
    fullPath
    __typename
  }
  offers(country: $country, platform: WEB) {
    ...SuggestedOffer
    __typename
  }
  __typename
}
'''

QUERY_SEARCH_PAGES = '''
query GetSuggestedTitles($country: Country!, $language: Language!, $first: Int!, $filter: TitleFilter,) {
  popularTitles(country: $country, first: $first, filter: $filter, ) {
    edges {
      node {
        ...SuggestedTitle
        __typename
      }
      __typename
    }
    __typename
  }
}
''' + FRAGMENT_SUGGESTED

QUERY_GET_MOVIE_BY_ID = '''
query GetSuggestedTitles($country: Country!, $language: Language!, $nodeId: ID!) {
    node(id: $nodeId) {
        ...SuggestedTitle
    }
}
''' + FRAGMENT_SUGGESTED

VARIABLES_GET_ALL_PACKAGES = {
    "iconFormat": "WEBP",
    "iconProfile": "S100",
    "platform": "WEB",
    "packagesCountry": "US",
    "monetizationTypes": []
}
