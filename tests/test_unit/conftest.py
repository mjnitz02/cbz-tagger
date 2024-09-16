import pytest


@pytest.fixture
def manga_name():
    return "Kanojyo to Himitsu to Koimoyou"


@pytest.fixture
def manga_request_response():
    # Abbreviated response for Kanojyo to Himitsu to Koimoyou
    return {
        "result": "ok",
        "response": "collection",
        "data": [
            {
                "id": "831b12b8-2d0e-4397-8719-1efee4c32f40",
                "type": "manga",
                "attributes": {
                    "title": {"en": "Oshimai"},
                    "altTitles": [
                        {"en": "4 Page Stories"},
                        {"en": "Oshi-Mai: Four Page Stories"},
                        {"en": "The 4 Pages"},
                        {"ja": "おしまい"},
                        {"ja": "お四枚"},
                        {"en": "Oshi-Mai: Four Page Storys"},
                    ],
                    "description": {"en": "A collection of twitter published manga by Kawasaki Tadataka..."},
                    "isLocked": False,
                    "links": {
                        "al": "119448",
                        "kt": "56601",
                        "mu": "176587",
                        "amz": "https://www.amazon.co.jp/gp/product/B084JRQCL3",
                    },
                    "originalLanguage": "ja",
                    "lastVolume": "",
                    "lastChapter": "",
                    "publicationDemographic": "seinen",
                    "status": "ongoing",
                    "year": 2020,
                    "contentRating": "suggestive",
                    "tags": [
                        {
                            "id": "423e2eae-a7a2-4a8b-ac03-a8351462d71d",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "Romance"},
                                "description": {},
                                "group": "genre",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                        {
                            "id": "4d32cc48-9f00-4cca-9b5a-a839f0764984",
                            "type": "tag",
                            "attributes": {"name": {"en": "Comedy"}, "description": {}, "group": "genre", "version": 1},
                            "relationships": [],
                        },
                        {
                            "id": "51d83883-4103-437c-b4b1-731cb73d786c",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "Anthology"},
                                "description": {},
                                "group": "format",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                        {
                            "id": "caaa44eb-cd40-4177-b930-79d3ef2afe87",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "School Life"},
                                "description": {},
                                "group": "theme",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                        {
                            "id": "e5301a23-ebd9-49dd-a0cb-2add944c7fe9",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "Slice of Life"},
                                "description": {},
                                "group": "genre",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                    ],
                    "state": "published",
                    "chapterNumbersResetOnNewVolume": False,
                    "createdAt": "2020-07-23T14:50:37+00:00",
                    "updatedAt": "2022-12-31T11:57:41+00:00",
                    "version": 15,
                    "availableTranslatedLanguages": ["en", "vi", "fr", "zh", "pt-br", "es-la", "id"],
                    "latestUploadedChapter": "9a8a1c1d-5b8f-4ad2-af34-f7d61200ef6d",
                },
                "relationships": [
                    {"id": "88259f42-5a70-4eff-b5f0-8687ab8844b9", "type": "author"},
                    {"id": "88259f42-5a70-4eff-b5f0-8687ab8844b9", "type": "artist"},
                    {"id": "be31ba9c-3490-41ea-b1bd-7f31cad7322f", "type": "cover_art"},
                ],
            },
            {
                "id": "f98660a1-d2e2-461c-960d-7bd13df8b76d",
                "type": "manga",
                "attributes": {
                    "title": {"en": "Kanojo to Himitsu to Koimoyou"},
                    "altTitles": [
                        {"en": "Let's Love Girlfriends and Secrets"},
                        {"ja": "カノジョと秘密と恋もよう"},
                        {"zh": "女朋友与秘密与恋爱模样"},
                        {"en": "Girlfriends and Secrets and Matters of the Heart"},
                        {"ja-ro": "Kanojyo to Himitsu to Koimoyou"},
                    ],
                    "description": {"en": "A yuri comedy between two girls who seem different but are ..."},
                    "isLocked": False,
                    "links": {
                        "al": "116918",
                        "ap": "kanojo-to-himitsu-to-koi-moyou",
                        "mu": "158719",
                        "amz": "https://www.amazon.co.jp",
                        "mal": "133320",
                    },
                    "originalLanguage": "ja",
                    "lastVolume": "2",
                    "lastChapter": "19",
                    "publicationDemographic": "seinen",
                    "status": "completed",
                    "year": 2019,
                    "contentRating": "safe",
                    "tags": [
                        {
                            "id": "4d32cc48-9f00-4cca-9b5a-a839f0764984",
                            "type": "tag",
                            "attributes": {"name": {"en": "Comedy"}, "description": {}, "group": "genre", "version": 1},
                            "relationships": [],
                        },
                        {
                            "id": "a3c67850-4684-404e-9b7f-c69850ee5da6",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "Girls' Love"},
                                "description": {},
                                "group": "genre",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                        {
                            "id": "e5301a23-ebd9-49dd-a0cb-2add944c7fe9",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "Slice of Life"},
                                "description": {},
                                "group": "genre",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                        {
                            "id": "eabc5b4c-6aff-42f3-b657-3e90cbd00b75",
                            "type": "tag",
                            "attributes": {
                                "name": {"en": "Supernatural"},
                                "description": {},
                                "group": "theme",
                                "version": 1,
                            },
                            "relationships": [],
                        },
                    ],
                    "state": "published",
                    "chapterNumbersResetOnNewVolume": False,
                    "createdAt": "2021-02-02T08:15:25+00:00",
                    "updatedAt": "2023-05-01T03:47:11+00:00",
                    "version": 30,
                    "availableTranslatedLanguages": ["en"],
                    "latestUploadedChapter": "b902c44d-cb34-4077-9501-c90b1216f2fb",
                },
                "relationships": [
                    {"id": "62b03b76-6565-4dab-b7d7-d38bce56808f", "type": "author"},
                    {"id": "62b03b76-6565-4dab-b7d7-d38bce56808f", "type": "artist"},
                    {"id": "af191279-8217-4f1b-a543-943b34af31d4", "type": "cover_art"},
                ],
            },
        ],
        "limit": 10,
        "offset": 0,
        "total": 2,
    }


@pytest.fixture
def manga_request_response_single(manga_request_response):
    return {
        "result": "ok",
        "response": "collection",
        "data": [manga_request_response["data"][0]],
        "limit": 10,
        "offset": 0,
        "total": 1,
    }


@pytest.fixture
def manga_request_content(manga_request_response):
    return manga_request_response["data"][0]


@pytest.fixture
def manga_request_id(manga_request_content):
    return manga_request_content["id"]


@pytest.fixture
def author_request_response():
    return {
        "result": "ok",
        "response": "collection",
        "data": [
            {
                "id": "88259f42-5a70-4eff-b5f0-8687ab8844b9",
                "type": "author",
                "attributes": {
                    "name": "Kawasaki Tadataka",
                    "imageUrl": None,
                    "biography": {},
                    "twitter": "https://twitter.com/tadataka_k",
                    "pixiv": "https://www.pixiv.net/users/101665",
                    "melonBook": None,
                    "fanBox": "https://tdtk.fanbox.cc/",
                    "booth": None,
                    "nicoVideo": None,
                    "skeb": None,
                    "fantia": "https://fantia.jp/fanclubs/26757",
                    "tumblr": None,
                    "youtube": None,
                    "weibo": None,
                    "naver": None,
                    "website": None,
                    "createdAt": "2021-04-19T21:59:45+00:00",
                    "updatedAt": "2022-06-25T16:13:21+00:00",
                    "version": 3,
                },
                "relationships": [
                    {"id": "4a817406-c99d-4698-9547-2ba234ec2644", "type": "manga"},
                    {"id": "432a1087-c60a-4f94-9b54-4b07cea6d964", "type": "manga"},
                    {"id": "6ca7089b-4049-491d-bd1b-594abc019986", "type": "manga"},
                    {"id": "1ace0492-4610-4b26-bfea-39ae80f79521", "type": "manga"},
                    {"id": "4c214865-bc40-4a07-9c08-8ff6fcd4e43b", "type": "manga"},
                    {"id": "96d95269-0844-4f8e-9947-71b26ff86127", "type": "manga"},
                    {"id": "937bfb69-1c3d-4b1b-8ca5-6fa5b21181aa", "type": "manga"},
                    {"id": "d9b0feaf-4201-4be0-8090-54cad946387d", "type": "manga"},
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "eb845697-fa13-43e8-b627-8cc65359cac2", "type": "manga"},
                ],
            }
        ],
        "limit": 10,
        "offset": 0,
        "total": 1,
    }


@pytest.fixture
def author_request_content(author_request_response):
    return author_request_response["data"][0]


@pytest.fixture
def author_request_id(author_request_content):
    return author_request_content["id"]


@pytest.fixture
def volume_request_response():
    return {
        "result": "ok",
        "volumes": {
            "none": {
                "volume": "none",
                "count": 3,
                "chapters": {
                    "none": {
                        "chapter": "none",
                        "id": "9a8a1c1d-5b8f-4ad2-af34-f7d61200ef6d",
                        "others": ["1e861031-03d2-4214-8276-62d5ee3db55c", "f7abd900-c30b-4f34-82f3-97adc9b9cb0a"],
                        "count": 3,
                    }
                },
            },
            "4": {
                "volume": "4",
                "count": 11,
                "chapters": {
                    "21": {
                        "chapter": "21",
                        "id": "ba86ddb7-c1d2-4be1-9bb7-9226731a827b",
                        "others": ["df5a487a-42ad-4914-950a-09da94f71afa"],
                        "count": 2,
                    },
                    "20": {
                        "chapter": "20",
                        "id": "64874b6f-37bd-4bba-9933-734e938f1798",
                        "others": [
                            "90bf3357-65f6-40d7-8a8a-d96a089558a8",
                            "63e8b2d2-200d-495d-a969-907fa7aef3c1",
                            "959dbdb1-1328-4bd1-9150-561bbd44dcf8",
                        ],
                        "count": 4,
                    },
                    "16": {
                        "chapter": "16",
                        "id": "487d289f-2193-45a2-8f11-fbdcfdc3b8e3",
                        "others": ["c31ae279-d4c5-4145-a478-a58a834a40d8", "937bdeac-5a97-4c9f-bef2-6480ab895501"],
                        "count": 3,
                    },
                    "13": {
                        "chapter": "13",
                        "id": "6085134c-c6d6-45ad-9f1c-175c814fd3d2",
                        "others": ["861a742b-35b9-4fb8-b4bd-d8a4621c2cc3"],
                        "count": 2,
                    },
                },
            },
            "3": {
                "volume": "3",
                "count": 3,
                "chapters": {
                    "3": {"chapter": "3", "id": "d9bbd5b5-2ce7-4bb6-bae0-3d5c04329f1d", "others": [], "count": 1},
                    "2": {"chapter": "2", "id": "c0a16578-0bc8-4f85-b31c-f8dfd796ef6b", "others": [], "count": 1},
                    "1": {"chapter": "1", "id": "d139dfa2-fcb7-40e4-b567-ce772aa739ea", "others": [], "count": 1},
                },
            },
            "2": {
                "volume": "2",
                "count": 45,
                "chapters": {
                    "19": {"chapter": "19", "id": "036ac830-2869-498c-a499-d0298e740d33", "others": [], "count": 1},
                    "18": {
                        "chapter": "18",
                        "id": "3e440772-abfd-4dde-bf1e-dce7f8931d7d",
                        "others": ["20ea9d79-45d0-4dc0-bbc5-9fa8f38af4e7"],
                        "count": 2,
                    },
                    "17": {
                        "chapter": "17",
                        "id": "5ab7f0f8-79c7-43b1-9463-f055ce60378c",
                        "others": ["d9a29a65-450e-4b57-9e89-81d919a39b18"],
                        "count": 2,
                    },
                    "16": {"chapter": "16", "id": "6ad25c1e-fb41-4171-ad63-161e473d2bf0", "others": [], "count": 1},
                    "15": {
                        "chapter": "15",
                        "id": "3b870386-fef8-466f-82de-c9341f00ffa6",
                        "others": ["6b28cdb2-f77f-463c-a037-0018ee6e1900"],
                        "count": 2,
                    },
                    "14": {
                        "chapter": "14",
                        "id": "41fe028d-f44f-4c10-b60b-17559b96a983",
                        "others": [
                            "c1b4c3b3-2268-4e79-b80a-24ff9a9241a4",
                            "384a8307-b2ed-45c6-9d45-ed5b29beea6b",
                            "59bb78c1-7825-4c44-9718-f35ea9dcc386",
                        ],
                        "count": 4,
                    },
                    "13": {
                        "chapter": "13",
                        "id": "4b6121a1-7eb2-4f69-b75f-a09985e845e4",
                        "others": ["3ccac6de-3280-4410-ac92-8d30a1e1232e", "67df3dfa-f7d3-4725-9e39-3c8c0760de56"],
                        "count": 3,
                    },
                    "12": {
                        "chapter": "12",
                        "id": "7c29f4ab-4ffa-4f0c-9afa-7282c42aad94",
                        "others": ["2771b355-1be9-4cdb-8b61-7b5623a2b1a1"],
                        "count": 2,
                    },
                    "11": {
                        "chapter": "11",
                        "id": "19020b28-67b1-48a2-82a6-9b7ad18a5c37",
                        "others": [
                            "21ecfe13-bef1-456e-b3e5-3892553ea844",
                            "9538a236-ce5f-4446-8103-b69305bcd312",
                            "eab7382d-c5fb-4bf0-93b5-8d1eca3428b0",
                        ],
                        "count": 4,
                    },
                    "10": {"chapter": "10", "id": "88fc6d13-3869-4d12-aa5e-f58d193b23af", "others": [], "count": 1},
                    "9": {"chapter": "9", "id": "c13950e5-6e64-4947-a959-bb0c9a9a0bb1", "others": [], "count": 1},
                    "8": {
                        "chapter": "8",
                        "id": "01c86808-46fb-4108-aa5d-4e87aee8b2f1",
                        "others": ["09a46a41-5f56-458b-8de0-5e0898c8ddaf"],
                        "count": 2,
                    },
                    "7": {
                        "chapter": "7",
                        "id": "90636936-4881-4354-b7f4-b77b3960d025",
                        "others": ["9420c57a-607c-4f1c-809b-acd2798ea02b"],
                        "count": 2,
                    },
                    "6": {
                        "chapter": "6",
                        "id": "909820a5-d5aa-4df0-902a-7ce49e8cfa14",
                        "others": ["2f380889-970f-4cda-90b4-c1633c8510a3", "aaf0668c-2796-4882-8e73-0dd12578d9c7"],
                        "count": 3,
                    },
                    "5": {
                        "chapter": "5",
                        "id": "9a1a4856-3668-4f9b-804b-46d80955f598",
                        "others": ["9eac91cf-696a-4456-a5a0-76738954632d"],
                        "count": 2,
                    },
                    "4": {
                        "chapter": "4",
                        "id": "fca19b9c-69b1-4215-879e-c428a641d6d1",
                        "others": ["9957915e-e182-4180-809a-c0a96a30efdf", "c3c9aab2-7160-4868-bb81-d3f0eab33301"],
                        "count": 3,
                    },
                    "3": {"chapter": "3", "id": "e4ac05fc-028f-4ab9-93a3-b216c7d6a3b8", "others": [], "count": 1},
                    "2": {
                        "chapter": "2",
                        "id": "890bb899-0e41-45be-bb95-dab9e93d5e09",
                        "others": ["e7b00636-c8da-402f-a765-98de234f6458"],
                        "count": 2,
                    },
                    "1": {
                        "chapter": "1",
                        "id": "607487aa-74c8-42e3-8183-cbe09b615c14",
                        "others": [
                            "04a4ec94-b33a-4e4b-9557-13876cfb23af",
                            "21108a8f-079b-4ded-ac37-557e49c994b1",
                            "3eaee688-2218-46ca-8982-67aaf48d21c2",
                            "1d90c952-5a3b-4b01-9194-c82f2ea702dd",
                            "2ea9e203-8106-40a9-b12a-a72bf0c58b07",
                            "da3cc8b1-567a-4b96-8f58-8835ed4200c5",
                        ],
                        "count": 7,
                    },
                },
            },
            "1": {
                "volume": "1",
                "count": 32,
                "chapters": {
                    "19": {"chapter": "19", "id": "84ba93c8-ab2f-40ca-87f8-0d18cc8453df", "others": [], "count": 1},
                    "18": {"chapter": "18", "id": "3152bd8d-ff86-4f65-89bd-81354ccc2d60", "others": [], "count": 1},
                    "17": {"chapter": "17", "id": "1d0a5c22-17ef-4277-9377-65cf720ad6e5", "others": [], "count": 1},
                    "16": {"chapter": "16", "id": "50fa7c10-083c-4649-a706-ffcd8c53225e", "others": [], "count": 1},
                    "15": {"chapter": "15", "id": "40d2d08f-acaf-4e0f-88d2-a65b7526df65", "others": [], "count": 1},
                    "14": {"chapter": "14", "id": "38688e1c-9ec8-4cad-b510-e159fed2d199", "others": [], "count": 1},
                    "13": {"chapter": "13", "id": "9b6f9c33-9047-4150-8721-32a13c45d636", "others": [], "count": 1},
                    "12": {"chapter": "12", "id": "a04251dc-46ee-4c62-905b-4114a7d69ee6", "others": [], "count": 1},
                    "11": {"chapter": "11", "id": "35b977fd-d9bb-414a-a3fc-61819072d134", "others": [], "count": 1},
                    "10": {"chapter": "10", "id": "a4d176e3-86e3-4a0d-9d1b-743c8295dc28", "others": [], "count": 1},
                    "9": {"chapter": "9", "id": "df23814c-bf44-4adb-baf8-dc3239638c1f", "others": [], "count": 1},
                    "8": {
                        "chapter": "8",
                        "id": "c7af939e-a012-4b47-926c-b280725f094f",
                        "others": ["e8ee0ac4-81a9-4870-b81f-3d929ea2c857"],
                        "count": 2,
                    },
                    "7": {
                        "chapter": "7",
                        "id": "6a129cf1-a85e-434d-851a-a2a1b177b2b8",
                        "others": ["e0f52b82-cf32-41bb-bd27-cc911d978a22"],
                        "count": 2,
                    },
                    "6": {
                        "chapter": "6",
                        "id": "877f5136-e830-4451-914e-c8a8be419009",
                        "others": ["f890a02e-deb2-440a-82e7-a1c7c98e54b9"],
                        "count": 2,
                    },
                    "5": {
                        "chapter": "5",
                        "id": "1361d404-d03c-4fd9-97b4-2c297914b098",
                        "others": ["1af12159-98d1-467d-a0f3-1ca54eb5de97"],
                        "count": 2,
                    },
                    "4": {
                        "chapter": "4",
                        "id": "f3b42a22-b613-42fb-b904-4c34e749a446",
                        "others": ["c43e6f7d-9131-4fd9-9a3a-f4b807a68ae1"],
                        "count": 2,
                    },
                    "3": {
                        "chapter": "3",
                        "id": "057c0bce-fd18-44ea-ad64-cefa92378d49",
                        "others": ["8fed590f-2683-4236-a43f-4654a5768c1f"],
                        "count": 2,
                    },
                    "2": {
                        "chapter": "2",
                        "id": "3e537cc4-ae47-47f0-a9c8-a3dd53c7f794",
                        "others": [
                            "3b304f52-0edc-49f8-a404-b6838537cba4",
                            "471a377d-f03c-4d06-bd5c-b0a4653ffdfc",
                            "228c1bd6-e43d-4921-904e-6a53b7e4f1f9",
                            "9b5d8e61-fcad-49be-a604-e00244213c60",
                        ],
                        "count": 5,
                    },
                    "1": {
                        "chapter": "1",
                        "id": "5b6d091b-2601-4dca-a1c3-e0729745a14d",
                        "others": [
                            "4fc565d3-d810-4fa5-bba4-abab4da34cb5",
                            "52f818a1-26dc-4a9f-98f7-d7f324e8e02e",
                            "e3240520-86b6-4181-a15c-9588e3e6142c",
                        ],
                        "count": 4,
                    },
                },
            },
        },
    }


@pytest.fixture
def cover_request_response():
    return {
        "result": "ok",
        "response": "collection",
        "data": [
            {
                "id": "be31ba9c-3490-41ea-b1bd-7f31cad7322f",
                "type": "cover_art",
                "attributes": {
                    "description": "",
                    "volume": "4",
                    "fileName": "87ad56cd-780b-48bc-82b1-fa425836f9a4.jpg",
                    "locale": "ja",
                    "createdAt": "2022-09-13T17:24:23+00:00",
                    "updatedAt": "2022-09-13T17:24:23+00:00",
                    "version": 1,
                },
                "relationships": [
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "f5d033a9-bb95-4be8-9edb-43b6fc0b5d70", "type": "user"},
                ],
            },
            {
                "id": "5d989a45-0946-4f22-9a79-53cc26e6e958",
                "type": "cover_art",
                "attributes": {
                    "description": "",
                    "volume": "2",
                    "fileName": "39194a9c-719b-4a27-b8ef-99a3d6fa0997.png",
                    "locale": "ja",
                    "createdAt": "2021-11-09T20:59:39+00:00",
                    "updatedAt": "2021-11-09T20:59:39+00:00",
                    "version": 1,
                },
                "relationships": [
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "f5d033a9-bb95-4be8-9edb-43b6fc0b5d70", "type": "user"},
                ],
            },
            {
                "id": "7be23c33-7b1e-4f2a-a9fe-ad3d6263f30f",
                "type": "cover_art",
                "attributes": {
                    "description": "",
                    "volume": "3",
                    "fileName": "a2b7bbe2-3a79-46a4-8960-e0e65a666194.jpg",
                    "locale": "ja",
                    "createdAt": "2021-11-09T20:59:39+00:00",
                    "updatedAt": "2021-11-09T20:59:39+00:00",
                    "version": 1,
                },
                "relationships": [
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "f5d033a9-bb95-4be8-9edb-43b6fc0b5d70", "type": "user"},
                ],
            },
            {
                "id": "9d64b6fb-0cac-4fa7-b3da-553fea602d2d",
                "type": "cover_art",
                "attributes": {
                    "description": "",
                    "volume": "1",
                    "fileName": "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg",
                    "locale": "ja",
                    "createdAt": "2021-05-24T18:04:01+00:00",
                    "updatedAt": "2021-11-09T20:59:36+00:00",
                    "version": 2,
                },
                "relationships": [
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "f8cc4f8a-e596-4618-ab05-ef6572980bbf", "type": "user"},
                ],
            },
            {
                "id": "9d64b6fb-0cac-4fa7-b3da-553fea602d2d",
                "type": "cover_art",
                "attributes": {
                    "description": "",
                    "volume": "1",
                    "fileName": "1d387431-eb38-40e9-bc6e-97e4ea4092dc.jpg",
                    "locale": "en",
                    "createdAt": "2021-05-24T18:04:01+00:00",
                    "updatedAt": "2021-11-09T20:59:36+00:00",
                    "version": 2,
                },
                "relationships": [
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "f8cc4f8a-e596-4618-ab05-ef6572980bbf", "type": "user"},
                ],
            },
        ],
        "limit": 10,
        "offset": 0,
        "total": 4,
    }


@pytest.fixture
def cover_request_content(cover_request_response):
    return cover_request_response["data"][0]


@pytest.fixture
def cover_request_content_png(cover_request_response):
    return cover_request_response["data"][1]


@pytest.fixture
def chapter_request_response():
    return {
        "result": "ok",
        "response": "collection",
        "data": [
            {
                "attributes": {
                    "chapter": "5",
                    "createdAt": "2020-05-26T22:55:31+00:00",
                    "externalUrl": None,
                    "pages": 4,
                    "publishAt": "2020-05-26T22:55:31+00:00",
                    "readableAt": "2020-05-26T22:55:31+00:00",
                    "title": "That Which Should Remain a Secret",
                    "translatedLanguage": "en",
                    "updatedAt": "2020-05-26T22:55:31+00:00",
                    "version": 1,
                    "volume": "1",
                },
                "id": "1361d404-d03c-4fd9-97b4-2c297914b098",
                "relationships": [
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "d2ae45e0-b5e2-4e7f-a688-17925c2d7d6b", "type": "user"},
                ],
                "type": "chapter",
            },
            {
                "attributes": {
                    "chapter": "3",
                    "createdAt": "2022-11-30T23:50:12+00:00",
                    "externalUrl": None,
                    "pages": 5,
                    "publishAt": "2022-11-30T23:50:13+00:00",
                    "readableAt": "2022-11-30T23:50:13+00:00",
                    "title": "Sœur aînée",
                    "translatedLanguage": "fr",
                    "updatedAt": "2022-11-30T23:50:15+00:00",
                    "version": 3,
                    "volume": "1",
                },
                "id": "057c0bce-fd18-44ea-ad64-cefa92378d49",
                "relationships": [
                    {"id": "caf4dae9-51a8-43c1-851e-939763f7cc98", "type": "scanlation_group"},
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "254631f2-c7ca-48a1-83f3-69579f782746", "type": "user"},
                ],
                "type": "chapter",
            },
            {
                "attributes": {
                    "chapter": "8",
                    "createdAt": "2021-01-25T22:49:05+00:00",
                    "externalUrl": None,
                    "pages": 4,
                    "publishAt": "2021-01-25T22:49:05+00:00",
                    "readableAt": "2021-01-25T22:49:05+00:00",
                    "title": "Super Tidy Moeri-Chan",
                    "translatedLanguage": "en",
                    "updatedAt": "2021-01-25T22:49:05+00:00",
                    "version": 1,
                    "volume": "2",
                },
                "id": "01c86808-46fb-4108-aa5d-4e87aee8b2f1",
                "relationships": [
                    {"id": "a6a88099-e02d-4671-8c88-e55d0af6041b", "type": "scanlation_group"},
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                    {"id": "f211e7c4-cf96-4f4b-ba3a-758e0f316b02", "type": "user"},
                ],
                "type": "chapter",
            },
            {
                "attributes": {
                    "chapter": "11",
                    "createdAt": "2020-05-23T17:21:04+00:00",
                    "externalUrl": None,
                    "pages": 5,
                    "publishAt": "2020-05-23T17:21:04+00:00",
                    "readableAt": "2020-05-23T17:21:04+00:00",
                    "title": "Asa no Miki senpai",
                    "translatedLanguage": "zh",
                    "updatedAt": "2021-07-13T08:28:01+00:00",
                    "version": 2,
                    "volume": "2",
                },
                "id": "19020b28-67b1-48a2-82a6-9b7ad18a5c37",
                "relationships": [
                    {"id": "8aaafe14-346e-404d-bc65-0d04e880bf04", "type": "scanlation_group"},
                    {"id": "831b12b8-2d0e-4397-8719-1efee4c32f40", "type": "manga"},
                ],
                "type": "chapter",
            },
        ],
        "limit": 10,
        "offset": 0,
        "total": 4,
    }


@pytest.fixture
def chapter_request_content(chapter_request_response):
    return chapter_request_response["data"][0]
