# 데이터 스키마 정의 (Data Schema Definition)

이 문서는 프로젝트에서 사용하는 데이터의 전체적인 구조를 정의합니다. 데이터는 하나의 JSON 객체이며, 그 안에 `works`와 `people`이라는 두 개의 주요 키를 가집니다.

## 최상위 구조 (Root Structure)

```json
{
  "works": { ... },
  "people": [ ... ]
}
```

| 키 (Key)  | 타입 (Type) | 설명 (Description)                               |
| --------- | ----------- | ------------------------------------------------ |
| `works`   | Object      | `songs`, `movies` 등 작품의 종류별로 묶인 객체입니다. |
| `people`  | Array       | 인물 정보를 담고 있는 객체들의 배열입니다.          |

---

## 1. `works` 객체

`works` 객체는 다양한 창작물들을 종류별로 분류하여 저장합니다.

```json
"works": {
  "songs": [
    { ... Song Object 1 ... }
  ],
  "movies": [
    { ... Movie Object 1 ... }
  ]
}
```

### 1.1. `Song` 객체 (in `works.songs`)

`Song` 객체는 노래 한 곡에 대한 정보를 나타냅니다.

| 키 (Key)         | 타입 (Type)          | 설명 (Description)                               | 예시 (Example)                  |
| ---------------- | -------------------- | ------------------------------------------------ | ------------------------------- |
| `title`          | String               | 노래의 제목                                      | `"라일락 (LILAC)"`              |
| `artist`         | String               | 노래를 부른 메인 아티스트 또는 그룹              | `"아이유 (IU)"`                 |
| `album`          | String               | 노래가 수록된 앨범의 이름                        | `"5th Album 'LILAC'"`           |
| `release_date`   | String               | 노래 발매일 (형식: `YYYY-MM-DD`)                 | `"2021-03-25"`                  |
| `contributions`  | Array<`Contribution`> | 이 노래에 기여한 인물들의 목록                   | `[ { ... }, { ... } ]`          |

#### `Contribution` 객체 (in `Song`)

| 키 (Key)        | 타입 (Type)        | 설명 (Description)                                     | 예시 (Example)              |
| --------------- | ------------------ | ------------------------------------------------------ | --------------------------- |
| `person_name`   | String             | 기여한 인물의 이름                                     | `"임수호"`                    |
| `roles`         | Array<String>      | 인물이 맡은 역할 목록.                                 | `["작곡", "편곡"]`          |

---

## 2. `people` 배열

`people` 배열은 각 인물에 대한 정보와 그들이 참여한 작품 목록을 담고 있습니다.

```json
"people": [
  { ... Person Object 1 ... },
  { ... Person Object 2 ... }
]
```

### 2.1. `Person` 객체 (in `people`)

`Person` 객체는 한 인물의 정보와 기여 목록을 나타냅니다.

| 키 (Key)         | 타입 (Type)                | 설명 (Description)                   |
| ---------------- | -------------------------- | ------------------------------------ |
| `person_name`    | String                     | 인물의 이름                          |
| `contributions`  | Array<`WorkContribution`>  | 해당 인물이 참여한 작품들의 목록     |

#### `WorkContribution` 객체 (in `Person`)

인물이 특정 작품에 어떤 역할로 기여했는지를 나타냅니다.

| 키 (Key)       | 타입 (Type)   | 설명 (Description)                                           | 예시 (Example)       |
| -------------- | ------------- | ------------------------------------------------------------ | -------------------- |
| `work_type`    | String        | 작품의 종류. `works` 객체의 키와 일치합니다 (`songs`, `movies` 등). | `"song"`             |
| `title`        | String        | 작품의 제목.                                                 | `"라일락 (LILAC)"`   |
| `roles`        | Array<String> | 해당 작품에서 맡은 역할 목록.                                | `["작사", "가창"]`   |

### `Person` 객체 예시

```json
{
  "person_name": "아이유 (IU)",
  "contributions": [
    {
      "work_type": "song",
      "title": "라일락 (LILAC)",
      "roles": ["작사", "가창"]
    },
    {
      "work_type": "drama",
      "title": "호텔 델루나",
      "roles": ["주연배우"]
    }
  ]
}
```