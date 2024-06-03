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
