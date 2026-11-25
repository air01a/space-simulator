# Encart « état de la fusée » — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher en bas à droite un dessin 2D vectoriel de l'engin piloté (étages, carburant, étage actif, largages), avec une silhouette réaliste d'Apollo.

**Architecture:** Les formes des pièces sont décrites dans les fichiers `.rocket` (sections `shape.<pièce>`), lues dans un objet `PartShape` stocké sur chaque `Stage_Composant`. Une fonction pure `layout_rocket` (sans Kivy, testable) calcule les rectangles en pixels ; un widget Kivy `RocketView` les dessine et ne redessine que si l'état change.

**Tech Stack:** Python 3.14, Kivy 2.3 (déjà utilisé), `unittest` de la bibliothèque standard (aucune dépendance ajoutée).

**Spec:** `docs/superpowers/specs/2026-11-25-rocket-panel-design.md`

## Global Constraints

- Aucune nouvelle dépendance (ni runtime ni test) : tests en `unittest`, lancés par `venv/bin/python -m unittest discover -s tests -t . -v` depuis la racine.
- Coût de l'encart < 0,5 ms par image ; la simulation doit rester à 60 images/s.
- Une fusée sans section `shape.*` se charge et s'affiche avec la forme par défaut.
- Unités des formes : mètres. Noms de pièces en minuscules (clés `configparser`).
- Valeurs par défaut : `length = 10`, `diameter = 3`, `top = none` (`fairing` si `payload`), `nozzles = 1` (0 si `payload`), `color = #d0d0d0`, `band = None`, `position = center`, `draw_below = None`, `enclosed = False`.
- `top` ∈ {`none`, `ogive`, `cone`, `fairing`, `capsule`, `capsule_les`} ; `position` ∈ {`center`, `side`}.
- `draw_below` ne change que le dessin, jamais l'ordre de largage.
- Pas de commit sans demande explicite de l'utilisateur : les étapes « Checkpoint » lancent les tests, sans `git commit`.
- `graphical/rocket_layout.py` et `rocketshape.py` ne doivent pas importer Kivy.

## Review Focus

1. Pièce sans carburant au départ (`payload`, carburant 0) : pas de division par zéro, `fuel` vaut `None` (pas de remplissage). → test dans la tâche 2.
2. Valeur invalide dans une section `shape.*` (`top = banane`, `length = abc`, couleur mal formée) : la clé fautive prend sa valeur par défaut, le chargement ne plante pas. → test dans la tâche 1.
3. Étage ne contenant que des boosters (`side`) sans pièce centrale : les boosters s'appuient sur le diamètre de la pièce centrale la plus basse, ou sur 0 s'il n'y en a aucune ; pas de plantage. → test dans la tâche 2.
4. Cible de `draw_below` absente, ou elle-même relocalisée : la pièce garde sa place normale, pas de boucle. → test dans la tâche 2.
5. Aucun engin piloté (`get_current_orbiter()` renvoie `None`, cf. crash corrigé précédemment) ou fenêtre redimensionnée : encart « None » sans plantage ; redessin à la nouvelle taille. → test dans la tâche 4.

---

### Task 1: Modèle de forme et chargement depuis les `.rocket`

**Files:**
- Create: `rocketshape.py`
- Modify: `orbiter.py` (`Stage_Composant.__init__`, `Load_Orbiters.get_orbiter`)
- Test: `tests/__init__.py` (vide), `tests/test_rocketshape.py`

**Interfaces:**
- Produces:
  - `rocketshape.PartShape` (dataclass) : `length: float`, `diameter: float`, `top: str`, `nozzles: int`, `color: tuple[float, float, float]` (0–1), `band: tuple | None`, `position: str`, `draw_below: str | None`, `enclosed: bool`.
  - `rocketshape.parse_shape(section: Mapping[str, str] | None, is_payload: bool) -> PartShape` : section `configparser` ou `None` ; valeurs invalides → défaut de la clé.
  - `rocketshape.parse_color(text: str) -> tuple[float, float, float]` (`#rrggbb`) ; lève `ValueError` si mal formé.
  - `Stage_Composant.shape: PartShape` (défaut `parse_shape(None, payload)`), `Stage_Composant.initial_carburant_mass: float`.

- [ ] **Step 1: Écrire les tests qui échouent** (`tests/test_rocketshape.py`)
  - `test_defaults` : `parse_shape(None, False)` == `PartShape(10, 3, "none", 1, parse_color("#d0d0d0"), None, "center", None, False)`.
  - `test_payload_defaults` : `parse_shape(None, True).top == "fairing"` et `.nozzles == 0`.
  - `test_parse_values` : section `{"length": "30.5", "diameter": "5.4", "top": "ogive", "nozzles": "5", "color": "#ffffff", "band": "#000000", "position": "side", "draw_below": "csm", "enclosed": "true"}` → champs correspondants (`color == (1.0, 1.0, 1.0)`, `enclosed is True`).
  - `test_invalid_values_fall_back` : `{"top": "banane", "length": "abc", "color": "blanc", "position": "dessus", "nozzles": "-2"}` → `top == "none"`, `length == 10`, `color` défaut, `position == "center"`, `nozzles == 1`.
  - `test_loaded_rocket_has_shapes` : `Load_Orbiters.get_orbiter` sur un fichier temporaire contenant `[param] name=T`, `[stage1] epc=270,4200,12300,220000,18`, `[shape.epc] length=30.5` → `stages.stages[0]["epc"].shape.length == 30.5` et `.initial_carburant_mass == 220000`.
  - `test_rocket_without_shapes_still_loads` : même fichier sans section `shape.*` → `shape == parse_shape(None, False)`.
  - `test_shape_follows_part` : après `Orbiters.separate_stage(orbiter, "booster1")` sur une fusée à 2 étages, le nouvel engin `booster1` a la même instance `shape` ; après `Orbiters.dock`, les pièces recopiées gardent leur `shape`.

- [ ] **Step 2: Vérifier l'échec** — Run: `venv/bin/python -m unittest tests.test_rocketshape -v` — Expected: `ModuleNotFoundError: No module named 'rocketshape'`.

- [ ] **Step 3: Implémenter `rocketshape.py`** (dataclass + `parse_shape` clé par clé avec `try/except` → défaut) **et brancher `orbiter.py`** : `Stage_Composant.__init__(..., payload=False, shape=None)` stocke `shape or parse_shape(None, payload)` et `initial_carburant_mass = carburant_mass` ; dans `get_orbiter`, passer `parse_shape(config["shape." + part] if présent else None, payload)`.

- [ ] **Step 4: Vérifier** — Run: `venv/bin/python -m unittest tests.test_rocketshape -v` — Expected: 7 tests OK.

- [ ] **Step 5: Checkpoint** — Run: `for s in scenario/ariane5.scn scenario/apollo.scn; do timeout 12 venv/bin/python main.py $s 2>&1 | grep -c Traceback; done` — Expected: `0` deux fois.

### Task 2: Mise en page pure (`layout_rocket`)

**Files:**
- Create: `graphical/rocket_layout.py`
- Test: `tests/test_rocket_layout.py`

**Interfaces:**
- Consumes: `Stages.stages` (liste de `dict[str, Stage_Composant]`, étage 0 = premier à brûler), `Stage_Composant.shape`, `.carburant_mass`, `.initial_carburant_mass`, `.throttle`, `.payload` ; `PartShape` (tâche 1).
- Produces:
  - `PartLayout` (dataclass) : `name: str`, `shape: PartShape`, `body: tuple[float, float, float, float]` (x, y, w, h en px), `top: tuple[float, float, float, float] | None`, `nozzles: list[tuple[float, float, float, float]]`, `fuel: float | None` (0–1), `state: str` (`"active"` | `"empty"` | `"idle"`).
  - `Fairing` (dataclass) : `cx: float`, `y0: float`, `w0: float`, `y1: float`, `w1: float`.
  - `RocketLayout` (dataclass) : `parts: list[PartLayout]` (ordre de dessin, de l'arrière vers l'avant), `fairings: list[Fairing]`, `scale: float` (px/m).
  - `layout_rocket(stages: list[dict], width: float, height: float, engine_on: bool = False, margin: float = 8) -> RocketLayout` ; coordonnées dans la boîte `(0, 0)–(width, height)`, y vers le haut.

Règles géométriques (en mètres avant mise à l'échelle) — décisions du plan :
- `length` = longueur totale de la pièce, haut compris ; hauteur du haut : `ogive` 1,2·d, `cone` 1,0·d, `fairing` 0,9·d, `capsule` 0,85·d, `capsule_les` 0,85·d + tour 2,5·d, `none` 0 ; corps = `max(0, length − haut)`.
- Tuyères : hauteur 0,15·d, largeur 0,3·d chacune, réparties sous le corps ; elles ne prennent pas de place dans la pile (elles passent derrière la pièce du dessous, dessinées avant elle), sauf celles de la pièce centrale la plus basse et des boosters, qui fixent le bas de la boîte englobante.
- Pile centrale : pièces `center` dans l'ordre (étage, puis fichier), de bas en haut, centrées sur x = 0.
- `draw_below` : retirer de la pile chaque pièce dont la cible est présente dans la pile et n'est pas elle-même relocalisée ; les réinsérer juste sous leur cible, dans l'ordre du fichier. Cible absente → place normale.
- `enclosed` : chaque suite consécutive de pièces `enclosed` dans la pile (après relocalisation) produit un `Fairing` du bas de la suite (largeur = diamètre de la pièce juste dessous, ou de la première pièce de la suite s'il n'y en a pas) au haut de la suite (largeur = diamètre de la pièce juste au-dessus, ou de la dernière pièce de la suite).
- Boosters (`side`) d'un étage i : base alignée sur la base de la première pièce centrale de l'étage i (à défaut, la pièce centrale la plus basse ; à défaut, y = 0) ; alternés gauche/droite, collés au corps de référence : x = ±(d_ref/2 + d_side/2) + rang·d_side.
- Échelle : `scale = min((width − 2·margin)/largeur_bbox, (height − 2·margin)/hauteur_bbox)`, fusée centrée horizontalement, posée sur `margin`.
- `fuel` = `carburant_mass / initial_carburant_mass` borné à [0, 1], `None` si `initial_carburant_mass <= 0`.
- `state` : `"active"` si étage 0, `engine_on`, `throttle > 0` et `carburant_mass > 0` ; `"empty"` si `initial_carburant_mass > 0` et `carburant_mass <= 0` ; sinon `"idle"`.
- Ordre de dessin (`parts`) : boosters, puis pile centrale du haut vers le bas (les tuyères d'une pièce passent ainsi derrière la pièce du dessous).

- [ ] **Step 1: Écrire les tests qui échouent** (`tests/test_rocket_layout.py`, avec une petite fabrique `make_stages([[("epc", shape, fuel, initial)], ...])`)
  - `test_stack_order_bottom_to_top` : 3 étages centraux → `body.y` croissant étage 0 < 1 < 2.
  - `test_fits_in_box_and_keeps_ratio` : toute coordonnée dans `[margin, width−margin]` × `[margin, height−margin]` ; rapport hauteur/largeur du corps d'une pièce = `(length−haut)/diameter` à 1e-6 près.
  - `test_side_boosters_left_and_right` : étage 0 = `booster1`, `booster2` (side) + `epc` → un booster à gauche du corps de l'EPC, l'autre à droite, bases au même y que l'EPC.
  - `test_only_side_parts` (Review Focus 3) : étage sans pièce centrale → pas d'exception, boosters dans la boîte.
  - `test_fuel_and_states` : `fuel == 0.25` pour 25 % ; `engine_on=True` → étage 0 `"active"`, étage 1 `"idle"` ; carburant 0 → `"empty"`.
  - `test_payload_without_fuel` (Review Focus 1) : `initial_carburant_mass == 0` → `fuel is None`, `state == "idle"`.
  - `test_draw_below_puts_lem_under_csm` : étages `s-ivb`, `csm`, `lem_descent` (`draw_below=csm`, `enclosed`), `lem_ascent` (idem) → ordre vertical `s-ivb < lem_descent < lem_ascent < csm` ; un seul `Fairing`, `w0` = largeur px du `s-ivb`, `w1` = largeur px du `csm`.
  - `test_draw_below_missing_target` (Review Focus 4) : sans `csm` → `lem_descent` et `lem_ascent` gardent leur ordre d'étage normal.
  - `test_draw_below_cycle` (Review Focus 4) : A `draw_below=B` et B `draw_below=A` → pas de boucle, les deux gardent leur ordre d'étage normal.
  - `test_empty_stages` : `layout_rocket([], 300, 450)` → `parts == []`, `fairings == []`.

- [ ] **Step 2: Vérifier l'échec** — Run: `venv/bin/python -m unittest tests.test_rocket_layout -v` — Expected: `ModuleNotFoundError: No module named 'graphical.rocket_layout'`.

- [ ] **Step 3: Implémenter `layout_rocket`** selon les règles ci-dessus (calcul en mètres, puis une seule passe de mise à l'échelle).

- [ ] **Step 4: Vérifier** — Run: `venv/bin/python -m unittest tests.test_rocket_layout -v` — Expected: 10 tests OK.

- [ ] **Step 5: Checkpoint** — Run: `venv/bin/python -m unittest discover -s tests -t . -v` — Expected: tous OK.

### Task 3: Formes des fusées fournies

**Files:**
- Modify: `rockets/ariane5.rocket`, `rockets/saturne5.rocket`, `rockets/saturne5_moon.rocket`, `rockets/satellite.rocket`
- Test: `tests/test_rocket_files.py`

**Interfaces:**
- Consumes: `Load_Orbiters.get_orbiter` (tâche 1), `layout_rocket` (tâche 2).

Valeurs (spec, section 4) — couleurs : blanc `#f2f2f2`, noir `#1e1e1e`, doré `#c9a227`, gris `#8c8c8c` :

| Fichier | Pièce | length | diameter | top | nozzles | color | band | position | autres |
|---|---|---|---|---|---|---|---|---|---|
| ariane5 | booster1, booster2 | 31 | 3 | ogive | 1 | blanc | — | side | |
| | epc | 30.5 | 5.4 | none | 1 | blanc | — | center | |
| | eps | 3.4 | 5.4 | none | 1 | gris | — | center | |
| | payload | 17 | 5.4 | fairing | 0 | blanc | — | center | |
| saturne5 | s-ic | 42 | 10 | none | 5 | blanc | noir | center | |
| | s-ii | 24.9 | 10 | none | 5 | blanc | — | center | |
| | s-ivb | 17.8 | 6.6 | none | 1 | blanc | noir | center | |
| | csm | 11 | 3.9 | capsule_les | 1 | gris | — | center | |
| | lem_descent | 3.2 | 4.2 | none | 1 | doré | — | center | `draw_below = csm`, `enclosed = true` |
| | lem_ascent | 2.8 | 4.0 | none | 1 | gris | — | center | `draw_below = csm`, `enclosed = true` |
| saturne5_moon | csm, lem_descent, lem_ascent | idem saturne5 | | | | | | | |
| satellite | payload | 3 | 2 | none | 0 | gris | doré | center | |

- [ ] **Step 1: Écrire les tests qui échouent** (`tests/test_rocket_files.py`)
  - `test_all_parts_have_shapes` : pour chaque fichier de `rockets/`, chaque pièce a une section `shape.<pièce>` (lire avec `configparser`).
  - `test_saturn_v_silhouette` : `layout_rocket` de `saturne5.rocket` → ordre vertical `s-ic < s-ii < s-ivb < lem_descent < lem_ascent < csm`, un `Fairing`.
  - `test_ariane5_boosters` : 2 boosters `side` de part et d'autre de l'EPC.
  - `test_moon_lem_after_csm_drop` : `saturne5_moon.rocket`, après `sep_part("csm")` → `lem_descent` en bas, aucun `Fairing`.

- [ ] **Step 2: Vérifier l'échec** — Run: `venv/bin/python -m unittest tests.test_rocket_files -v` — Expected: FAIL (`shape.epc` absent…).

- [ ] **Step 3: Ajouter les sections `shape.*`** du tableau dans les 4 fichiers (sans toucher aux sections `stageN`).

- [ ] **Step 4: Vérifier** — Run: `venv/bin/python -m unittest discover -s tests -t . -v` — Expected: tous OK.

- [ ] **Step 5: Checkpoint** — même commande que tâche 1 étape 5, plus `scenario/apollo_moon_orbit.scn` — Expected: `0` partout.

### Task 4: Widget `RocketView` et intégration à l'écran

**Files:**
- Create: `graphical/rocket.py`
- Modify: `display.py` (`Graphics.init`, `Graphics.draw`)
- Test: `tests/test_rocket_view.py`

**Interfaces:**
- Consumes: `layout_rocket`, `RocketLayout`, `PartLayout`, `Fairing` (tâche 2) ; `Orbiter.stages.stages`, `Orbiter.engine_on`, `Orbiter.name`.
- Produces:
  - `RocketView(Widget)` dans `graphical/rocket.py`, avec `update(orbiter: Orbiter | None) -> bool` (True si redessiné) et `state_key(orbiter: Orbiter | None) -> tuple` (fonction de module, sans Kivy : nom, taille du widget, `engine_on`, et pour chaque pièce `(étage, nom, round(fuel·100) ou None, state)`).

Rendu (le développeur choisit traits, police, proportions exactes des formes de haut) :
- Fond `Color(0, 0, 0, 0.55)` + bord fin ; nom de l'engin en haut (ou « None »), police `int(Window.height / 800 * 14)`.
- Par pièce, dans l'ordre de `parts` : tuyères (gris foncé), corps `shape.color` avec bande claire à gauche et sombre à droite, bandes `band` (2 bandes horizontales), remplissage carburant plus sombre de bas en haut sur `fuel·h`, haut selon `shape.top`. `"empty"` : couleurs désaturées (moyenne avec le gris 50 %). `"active"` : contour `Color(1, 0.75, 0.2)`. Pourcentage de carburant à droite des pièces `"active"`.
- `Fairing` : trapèze `Color(0.9, 0.9, 0.9, 0.25)` + contour, dessiné après les pièces qu'il contient.
- Position/taille : mises à jour dans `Graphics.draw` depuis `Window.size` : `h = 0.375·Window.height`, `w = h·2/3`, `pos = (self.right − w − 10, self.y + 10)` (bas droit de la zone `Graphics`, au-dessus des bandeaux d'information).
- `Graphics.init` : `self.rocket_view = RocketView()` ajouté à `self.ids.dynamics` après `draw_trajectory`. `Graphics.draw` : `self.rocket_view.update(orbiters.get_current_orbiter())`.

- [ ] **Step 1: Écrire les tests qui échouent** (`tests/test_rocket_view.py`, sans fenêtre : tester `state_key`)
  - `test_key_stable_when_nothing_changes` : deux appels sur le même engin → clés égales.
  - `test_key_changes_on_fuel_percent_sep_and_engine` : clé différente après −1 % de carburant, après `sep_part`, après `engine_on = True`.
  - `test_key_none_orbiter` (Review Focus 5) : `state_key(None)` ne lève pas d'exception.

- [ ] **Step 2: Vérifier l'échec** — Run: `venv/bin/python -m unittest tests.test_rocket_view -v` — Expected: `ImportError` sur `state_key`.

- [ ] **Step 3: Implémenter `state_key` et `RocketView`** (redessin complet du canvas seulement si `state_key` a changé) **et l'intégration dans `display.py`**.

- [ ] **Step 4: Vérifier les tests** — Run: `venv/bin/python -m unittest discover -s tests -t . -v` — Expected: tous OK.

- [ ] **Step 5: Vérifier dans l'appli** — Captures avec le script du scratchpad `shot.py` (scénarios `ariane5.scn`, `apollo.scn`, `apollo_moon_orbit.scn`) : l'encart est en bas à droite, Ariane 5 avec ses 2 boosters, Saturn V avec le LEM sous le CSM dans l'adaptateur. Puis, dans un script Kivy : largage des boosters d'Ariane (`separate_stage` ×2) → l'encart se met à jour ; dernier engin crashé → « None » sans erreur ; fenêtre redimensionnée → encart redessiné.

- [ ] **Step 6: Mesurer le coût** — Profilage `prof_app.py` (moteur allumé, 15 s) : `RocketView.update` < 0,5 ms médiane par image, `draw` toujours à ~60/s. Résultat chiffré reporté à l'utilisateur.

- [ ] **Step 7: Checkpoint** — tous les tests + les 3 scénarios sans `Traceback`.
