ALONEHUNTER — R020 SHOT003 — COMPLETE REPRODUCIBLE RUNBOOK V1

ЦЕЛЬ

Этот документ сохраняет полный технический маршрут SHOT003: что было authority, какие маршруты исследовались, какие provider jobs были ошибочными/неприемлемыми, какой путь реально дал принятый SHOT003 V2, какие exact IDs/SHA/размеры необходимо использовать при recovery и какие действия запрещено повторять.

КРИТИЧЕСКОЕ ПРАВИЛО RECOVERY

Не восстанавливать SHOT003 по памяти чата.

Не начинать заново с Kaggle/FramePack.

Не перерендеривать принятый V2.

Текущий принятый binary является source of truth:

Drive ID: 1hNY1X6WxNebyt91Ha65-MHbI-M4sC6Ir

Filename: AH_R020_SHOT003_LOCAL_MICROGESTURE_V2.mp4

Bytes: 632252

SHA256: b2632b34260a8d9eb1201aae89cf4e611cdcbf3c8502146dca38d1b684bc1c2e

Geometry: 1080x1920

Frames: 96

FPS: 24

Duration: 4.000 s

Visual QA: PASS

HQ QA: PASS

1. SHOT CONTRACT / SEMANTIC TARGET

SHOT003 должен был быть статичным medium shot через существующий дверной проём.

Мир/квартира не должны плыть.

Медная труба, стены, дверной проём, велосипед и пространственная геометрия должны оставаться неизменными.

Камера locked: запрещены pan, tilt, zoom, dolly, reframing и camera-trick вместо действия человека.

Герой остаётся в закрытой позе.

Единственное читаемое действие: короткий restrained dismissive half-gesture верхней частью тела/предплечьем; жест начинается, становится читаемым и затем останавливается.

Нельзя превращать его в размашистый/мелодраматический жест.

2. EXACT SOURCE / REFERENCE FAMILY

Основной SHOT003 source:

Reference B Drive ID: 18JjpKKLZgOorflYEp06GuFFen61eIs2K

Bytes: 463048

SHA256: 17ac9f5d4ef6aca950a9587cbd49b7db1e2a0dc67f6e6f05e0146a67aea1e2c1

Reference family была восстановлена как A/B/C, но для рабочей линии SHOT003 использовался именно Reference B.

Любой новый execution обязан сначала проверить exact bytes + SHA256 source.

Если identity source не совпадает — fail closed.

3. РАННИЙ FRAMEPACK / KAGGLE МАРШРУТ

Canonical FramePack control plane:

Make scenario 6283680

Функция: FramePack start / Kaggle push

Graph: StartSubscenario -> HTTP MakeRequest -> ReturnData

Kaggle endpoint:

https://www.kaggle.com/api/v1/kernels/push

Kaggle Basic Auth keychain в Make: 210371

Форма provider payload:

{

  "kernelSlug": "...",

  "newTitle": "...",

  "text": "<python bootstrap>",

  "language": "python",

  "kernelType": "script",

  "isPrivate": true,

  "enableGpu": true,

  "enableInternet": true,

  "machineShape": "NvidiaTeslaT4"

}

Companion terminal callback:

Make scenario 6300036

Отдельный admission ingress:

Make scenario 6281838

Webhook ID: 2816032

Его роль: admission ingress, а не renderer.

Он не должен считаться доказанным shot executor сам по себе.

4. ПОЧЕМУ НЕЛЬЗЯ БЫЛО ПРОСТО ИСПОЛЬЗОВАТЬ 6283680

Physical readback 6283680 доказал, что его immutable payload был жёстко SHOT001-bound:

source = SHOT001 source;

prompt = SHOT001 exposure-reveal prompt;

output = AH_R020_SHOT001_FRAMEPACK.mp4.

Поэтому запуск SHOT003 через 6283680 с одним лишь новым kernel slug был семантически ложным.

Полученный Kaggle job 136342585 был отвергнут как SHOT003 независимо от имени job.

DO_NOT_REPEAT: не считать новое имя kernel доказательством нового shot payload.

5. SHOT-LOCAL FRAMEPACK BOOTSTRAP, КОТОРЫЙ БЫЛ ПОДГОТОВЛЕН

GitHub repository:

AloneHunterr/alonehunter-lab2

Working branch:

r020-shot003-framepack-bootstrap-20260929

Ключевые commits:

f9fd4b83c698e3aaac13c5cf373616a58821827c — shot-local Reference-B bootstrap

d3fce0ddb338548b9859b806ea3c61ac8b77022e — bootstrap bound to canonical FramePack terminal callback

Файлы:

framepack/kaggle/framepack_inference.py

framepack/kaggle/r020_shot003_bootstrap.py

framepack/kaggle/control_plane_v1.py

Ключевая логика bootstrap:

TASK='AH_VIDEO_STABILIZATION_V1_V2_20260927__R020_SHOT003'

SOURCE_ID='18JjpKKLZgOorflYEp06GuFFen61eIs2K'

SOURCE_BYTES=463048

SOURCE_SHA256='17ac9f5d4ef6aca950a9587cbd49b7db1e2a0dc67f6e6f05e0146a67aea1e2c1'

Source downloaded to:

/kaggle/working/R020_REFERENCE_B.jpg

После download:

if source bytes != 463048 -> fail

if sha256 != exact source SHA -> fail

Environment passed into runner:

AH_VIDEO_TASK_ID

AH_VIDEO_SOURCE_ID

AH_VIDEO_SOURCE_SHA256

AH_VIDEO_SOURCE_PATH

AH_VIDEO_PROMPT

AH_VIDEO_OUTPUT='AH_R020_SHOT003_FRAMEPACK.mp4'

AH_FRAMEPACK_RECEIPT_URL=<canonical FramePack callback>

Shot-local prompt смысл:

static medium through existing doorway;

preserve exact old-apartment geometry;

preserve peeling wall/radiator/doorframe/copper-pipe topology;

hero remains alone and closed;

one restrained dismissive half-gesture;

subtle shoulder/forearm motion only;

locked camera;

no pan/tilt/zoom/dolly/reframing;

no new objects;

no pipe morphing;

no architecture drift;

photorealistic.

6. GENERIC KAGGLE CONTROL ROUTE

Когда Make refused создание нового large inline scenario, был восстановлен generic Kaggle push scenario:

Make 6176378

Его provider module также использует:

POST https://www.kaggle.com/api/v1/kernels/push

Basic Auth keychain 210371

Он принимает:

kernel_id

kernel_slug

kernel_title

text_escaped

Через него был отправлен correct Reference-B FramePack job:

Make execution: 371e38e6689a46eb8d4e2bc5dc114ec8

Kaggle kernel: 136608941

Version: 1

HTTP: 200

Ref: /code/alonehunter/ah-r020-shot003-framepack-reference-b

После single submit generic launcher был деактивирован.

Этот provider job не стал финальным production result: terminal callback не был получен, а позднее successful local route superseded необходимость его продолжать.

DO_NOT_REPEAT: не возрождать 136608941 и не делать blind retry.

7. ФИНАЛЬНЫЙ УСПЕШНЫЙ ПУТЬ — ZERO-COST LOCAL MICRO-GESTURE

Фактически принятый SHOT003 был создан не старым Kaggle job, а локальной bounded обработкой exact Reference B.

Основные инварианты successful local route:

— exact Reference B;

— 1080x1920;

— 96 frames;

— 24 fps;

— 4.000 s;

— camera fixed;

— background/world fixed;

— motion только внутри локальной upper-body/person области;

— outside-mask pixels должны сохраняться точно до encode;

— никаких paid providers;

— никаких повторных world generations.

V1 output:

AH_R020_SHOT003_LOCAL_MICROGESTURE_V1.mp4

Bytes: 2486025

SHA256: eadde3408b544b8bd062c2275c0fe4763de7c6b52abc260a5ad3fa3c7e089bd8

1080x1920 / 96f / 24fps / 4.000s

V1 technical preservation:

motion confined to feathered person upper-body region;

pre-encode outside-mask max pixel diff = 0;

outside-mask exact = true;

mid-gesture changed 92358 in-mask pixels;

max in-mask diff = 153;

no camera motion.

Visual QA result V1:

PRESERVATION PASS

SEMANTIC MOTION FAIL

Причина: жест был слишком слабым и воспринимался как дыхание/микродрожание, а не как читаемый dismissive half-gesture.

Это важный negative-evidence case:

если мир сохранён идеально, но действие не читается, binary всё равно FAIL.

8. DISCOVERABILITY REPAIR V1

V1 сначала существовал физически, но receiver не мог получить binary.

Запрещённый ответ на это: новый рендер.

Правильный ответ: доставка того же SHA.

Source Library full ID:

libfile_b5c889107a68819196cb4785700663ae

Byte-identical discoverable Drive copy:

Drive ID: 16gGG9OsPXKJYF30HsDSTHdEHFd9eRj1X

Parent: 1GvX6E1ICfnyIuItP2SkCWUsTLmuLUVa5

После upload:

bytes = 2486025

SHA256 = eadde3408b544b8bd062c2275c0fe4763de7c6b52abc260a5ad3fa3c7e089bd8

Именно после этого Visual смог физически проверить 96 кадров.

9. V2 — УЗКАЯ КОРРЕКЦИЯ, КОТОРАЯ ПРОШЛА

После Visual FAIL не переделывались:

scene;

camera;

apartment;

copper pipe;

lighting;

background;

shot duration;

frame count;

fps.

Менялся только local gesture readability.

Known exact V2 temporal envelope:

frames 0-18: unchanged / исходная закрытая поза

frames 19-42: smooth ramp к более читаемому upper-body/forearm dismissive half-gesture

frames 42-95: stopped end pose / hold

Known local ROI from durable receipt:

x = 780..1079

y = 500..1109

Pre-encode pixels outside this ROI:

max diff = 0

exact = true

V2 output:

AH_R020_SHOT003_LOCAL_MICROGESTURE_V2.mp4

Bytes: 632252

SHA256: b2632b34260a8d9eb1201aae89cf4e611cdcbf3c8502146dca38d1b684bc1c2e

1080x1920 / 96f / 24fps / 4.000s

Library:

file_id file_00000000f614820aa8636c2087156847

library_file_id libfile_432c244715fc8191824d8312895c17a2

Drive:

1hNY1X6WxNebyt91Ha65-MHbI-M4sC6Ir

Drive parent:

1GvX6E1ICfnyIuItP2SkCWUsTLmuLUVa5

Source and Drive copies были независимо hash-checked и совпали byte-for-byte.

10. ВАЖНО О ТОЧНОМ ЛОКАЛЬНОМ СИНТАКСИСЕ

Полный ephemeral Python notebook/script, которым был сделан локальный V1/V2, не был durably сохранён строка-в-строку.

Поэтому нельзя честно утверждать byte-for-byte reconstruction исходного скрипта.

Что сохранено физически и является достаточным для route reconstruction:

exact source identity;

output identities;

geometry/fps/frame count/duration;

local ROI V2;

frame envelope V2;

outside-ROI exactness;

semantic motion contract;

Visual/HQ receipts.

Реконструкционный алгоритм должен быть таким:

frame = exact Reference B

roi = frame[500:1110, 780:1080]

mask = feathered person/upper-body alpha mask inside ROI

Для каждого frame index i:

if i <= 18:

    motion_strength = 0

elif 19 <= i <= 42:

    t = (i - 19) / (42 - 19)

    motion_strength = smoothstep(t)

else:

    motion_strength = 1

Применить только к masked upper-body/forearm region:

small restrained affine/deformation displacement;

torso remains closed;

forearm motion is visibly dismissive but partial;

no displacement outside local person region.

Composite:

output = source.copy()

output[ROI] = alpha * moved_person + (1-alpha) * original_ROI

Hard validator before encode:

outside_roi_diff_max == 0

camera transform == identity

frame geometry == 1080x1920

Encode target:

24 fps

96 frames

4.000 s

H.264/MP4 or equivalent production-compatible mp4

ВАЖНО:

Этот блок — functionally faithful reconstruction guidance по durable receipts, но не claims of original byte-identical source code.

Для релиза принятый V2 binary следует переиспользовать, а не пытаться воспроизвести его из этого skeleton.

11. RECOMMENDED REPRODUCTION SKELETON

Псевдосинтаксис Python/OpenCV:

import cv2

import numpy as np

src = cv2.imread("R020_REFERENCE_B.jpg")

assert src.shape[:2] == (1920,1080)

x0,y0,x1,y1 = 780,500,1080,1110

base = src.copy()

frames = []

for i in range(96):

    if i <= 18:

        k = 0.0

    elif i <= 42:

        t = (i-19)/23.0

        k = t*t*(3-2*t)

    else:

        k = 1.0

    out = base.copy()

    # person_mask must be local and feathered.

    # Exact original deformation parameters are NOT durably preserved.

    # Use minimal affine/local warp only on the upper-body/forearm.

    moved_roi = bounded_person_motion(base[y0:y1,x0:x1], k)

    out[y0:y1,x0:x1] = alpha_composite(

        base[y0:y1,x0:x1],

        moved_roi,

        person_mask

    )

    assert np.max(abs_diff_outside_roi(out, base, x0,y0,x1,y1)) == 0

    frames.append(out)

writer = cv2.VideoWriter(

    "AH_R020_SHOT003_LOCAL_MICROGESTURE_V2.mp4",

    cv2.VideoWriter_fourcc(*"mp4v"),

    24,

    (1080,1920)

)

for f in frames:

    writer.write(f)

writer.release()

После encode обязательно:

ffprobe geometry/fps/duration/frame count

sha256sum

bytes

temporal frame samples

outside-world preservation QA

Visual QA

HQ QA

12. QA ROUTE, КОТОРЫЙ РЕАЛЬНО СРАБОТАЛ

Big Tech binary/source-preservation QA

- проверяет exact source identity;

- dimensions/frame count/fps/duration;

- local edit confinement;

- outside-mask/world preservation;

- SHA/bytes.

Visual Studio independent perceptual QA

V1 verdict:

VISUAL_QA_FAIL__SEMANTIC_MOTION_INSUFFICIENT__PRESERVATION_PASS

V2 verdict:

VISUAL_QA_PASS__SHOT003_V2__SEMANTIC_GESTURE_READABLE__PRESERVATION_PASS

Visual V2 sampling:

frames 0 / 9 / 18 / 24 / 30 / 36 / 42 / 60 / 95

plus enlarged person-region review.

Producer HQ final independent QA:

HQ_QA_PASS__SHOT003_V2_ACCEPTED

HQ independently verified:

same Drive binary;

same SHA;

same bytes;

1080x1920;

96f;

24fps;

4.000s;

world continuity;

copper pipe;

wall/corridor/bicycle;

no camera travel;

no obvious world warp;

no mask seam/topology drift;

gesture begins from closed posture, develops, then holds.

13. CANONICAL HANDOFF CHAIN

HANDOFF 109148

V1 local render complete / binary preservation PASS / Visual required.

HANDOFF 109149

Durable artifact registration.

HANDOFF 109151

HQ correction: binary exists; supersedes old NO_BINARY.

HANDOFF 109154

V1 discoverability repaired to Drive exact same SHA.

HANDOFF 109155

Visual V1 FAIL: semantic motion insufficient; preservation PASS.

HANDOFF 109156

One bounded V2 correction completed.

HANDOFF 109157

V2 discoverability repaired to Drive exact same SHA.

HANDOFF 109158

Visual V2 PASS.

HANDOFF 109159

HQ V2 PASS / SHOT003 accepted.

14. DO_NOT_REPEAT

Do not rerender accepted SHOT003 V2.

Do not revive Kaggle 136342585.

Do not revive Kaggle 136608941 unless a future forensic audit explicitly needs provider evidence.

Do not mutate canonical SHOT001 scenario 6283680.

Do not use camera travel to fake human gesture.

Do not regenerate the apartment/world when only actor motion is defective.

Do not change copper-pipe topology.

Do not treat API 200/job-created as shot success.

Do not treat binary existence as Visual QA.

Do not treat Visual PASS as HQ PASS.

Do not create a new render merely because Library/Files cannot discover the exact binary; repair discoverability and preserve SHA.

Do not use a truncated Library ID as exact identity when the full id is available.

Do not promote V1; V1 remains negative evidence only.

Do not substitute a different V2 binary: exact SHA b2632b34...bc1c2e is the accepted one.

15. RECOVERY ORDER FOR A NEW CHAT

1. Read SYSTEM STATE.

2. Resolve R020 task and latest HANDOFFs.

3. Read this runbook.

4. Resolve exact accepted V2 Drive ID 1hNY1X6WxNebyt91Ha65-MHbI-M4sC6Ir.

5. Verify bytes + SHA before any downstream action.

6. Treat SHOT003 as HQ_QA_PASS.

7. Move only to the next already-authored canonical shot contract.

8. Never invent SHOT004 semantics; resolve storyboard/Visual authority first.

16. MINIMUM STATE SNAPSHOT

SHOT003 accepted binary:

Drive 1hNY1X6WxNebyt91Ha65-MHbI-M4sC6Ir

SHA256 b2632b34260a8d9eb1201aae89cf4e611cdcbf3c8502146dca38d1b684bc1c2e

632252 B

1080x1920

96 frames

24 fps

4.000 s

Visual PASS

HQ PASS

Source Reference B:

Drive 18JjpKKLZgOorflYEp06GuFFen61eIs2K

463048 B

SHA256 17ac9f5d4ef6aca950a9587cbd49b7db1e2a0dc67f6e6f05e0146a67aea1e2c1

Final rule:

PRESERVE ACCEPTED BINARY. RECOVER BEFORE REBUILD. QA EACH LAYER SEPARATELY. DELIVERY FAILURE IS NOT RENDER FAILURE.