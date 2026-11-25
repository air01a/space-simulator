# Rentrée atmosphérique, bouclier, parachute — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** destruction à la rentrée des engins sans bouclier, CM/SM séparés, parachute automatique, et animations (plasma, désintégration, parachute) dans l'encart de la fusée.

**Architecture:**
- **Physique sans Kivy, testable :**
  - `equipment.py` : lecture des sections `[equipment.*]` ;
  - `reentry.py` : flux, charge thermique, logique de déploiement du parachute.
- **Intégration** dans `Orbiter.update_position`, avec l'attribut `destroyed`.
- **Géométrie des animations** dans des modules purs :
  - `graphical/plasma.py`, `graphical/parachute.py`, `graphical/breakup.py`.
  - Ils sont dessinés par `RocketView` dans `canvas.after`, en réutilisant les maillages, comme les flammes.

**Tech Stack:** Python 3.14, numpy, Kivy, unittest.

**Spec:** docs/superpowers/specs/2026-11-25-reentry-parachute-design.md

## Global Constraints

- **Flux** : q̇ = 1.7415e-4 · √(ρ/Rn) · v³ (W/m²).
- **Charge thermique** : Q ← Q·exp(−dt/τ) + q̇·dt.
- **Destruction** : si Q > Q_max et qu'aucune pièce n'a de bouclier.
- **Calibrage** :
  - un étage nu qui rentre depuis l'orbite basse (environ 7,8 km/s) est détruit entre 70 et 85 km ;
  - les montées de Saturn V, d'Ariane 5 (mission) et de M51 restent sous Q_max/2.
- **Parachute** :
  - `parachute = diamètre, nombre, altitude de déploiement, vitesse max` ;
  - traînée 0,8·n·π(d/2)², avec une montée progressive sur 3 s ;
  - déploiement si l'altitude est sous l'altitude prévue, si l'engin descend et si sa vitesse est sous la vitesse max ;
  - jamais rétracté.
- **CM d'Apollo** : `heat_shield = yes`, `parachute = 25.4, 3, 3000, 200`.
- **Masses** :
  - SM : 3 000 kg à vide, avec 21 500 kg de carburant (saturne5) ou 6 300 kg (saturne5_moon) ;
  - CM : 5 500 kg, sans carburant ;
  - traînée de 15 chacun.
- **Plasma visible** au-delà de 50 kW/m².
- **Désintégration** : environ 2,5 s. **Parachute** : ouverture en 3 s.
- **Temps accéléré** : plafonné à ×10 quand un engin en mouvement est dans une atmosphère.
- **Fluidité** : au moins 55 images/s, mesuré.

## Review Focus

1. **Le CM ne doit pas être séparé automatiquement** par le contrôleur de mission. Aujourd'hui, une pièce sans carburant passe dans `empty_part`.
2. **Réglage du seuil de destruction** :
   - une pièce détruite en pleine montée est un échec, à vérifier sur trois lanceurs ;
   - une pièce jamais détruite en rentrée aussi.
3. **La destruction de l'engin contrôlé ne doit pas planter** l'interface : sélecteur, panneau, `Control`.
4. **Une rentrée en temps accéléré au-delà de ×10** ne doit pas traverser l'atmosphère sans échauffement.
5. **Les parties de l'interface qui lisent `CSM`** doivent toutes passer sur la nouvelle séparation, sans casse. Ça concerne `draw_below`, les tests et `saturne5_moon`.

---

### Task 1 : équipement des pièces

**Files:**
- Create : `equipment.py`, `tests/test_equipment.py`
- Modify : `orbiter.py`, avec :
  - le chargement ;
  - les attributs `Stage_Composant.heat_shield` et `.parachute` ;
  - dans `get_thrust`, une pièce sans réservoir initial n'est jamais marquée comme vide.

**Interfaces produites :**
- `parse_equipment(section) -> Equipment(heat_shield: bool, parachute: Parachute | None)`
- `Parachute(diameter, count, deploy_altitude, max_speed)`

**Tests :**
- valeurs lues ;
- valeurs par défaut ;
- valeur invalide qui retombe sur le défaut ;
- section en majuscules ;
- une pièce sans réservoir n'entre jamais dans `empty_part`.

### Task 2 : séparation CM / SM

**Files:**
- Modify :
  - `rockets/saturne5.rocket` et `rockets/saturne5_moon.rocket` ;
  - `orbiter.py`, avec `Orbiters.separate_full_stage` qui fait partir ensemble les pièces centrales d'un étage, en un engin « A+B » empilé ;
  - `tests/test_rocket_files.py`, `tests/test_rocketshape.py`.

**Tests :**
- l'ordre du dessin de Saturn V, avec le CM au sommet et le LEM sous le SM ;
- le largage de l'étage SM/CM donne un seul engin « sm+cm » à 2 étages ;
- un second largage laisse le CM seul ;
- Ariane 5 est inchangée ;
- les masses totales sont inchangées.

### Task 3 : échauffement et destruction

**Files:**
- Create : `reentry.py`, `tests/test_reentry.py`
- Modify : `orbiter.py`, avec :
  - `heat_load`, `heat_flux`, `destroyed` ;
  - `has_heat_shield()`, `in_atmosphere()` ;
  - la mise à jour par sous-pas dans `update_position`.
- Modify : `spacetime.py`, avec :
  - un engin dans l'atmosphère est calculé pas à pas et l'accélération est plafonnée à ×10 ;
  - le message « destroyed by reentry ».

**Rn** = rayon du plus gros diamètre de la pile.

**Tests :**
- valeur de référence de Sutton-Graves ;
- décroissance de la charge ;
- calibrage, à l'altitude de destruction mesurée :
  - une rentrée orbitale détruit un S-IVB nu entre 70 et 85 km ;
  - le CM seul survit ;
  - le SM seul est détruit ;
- les trois montées nominales restent sous Q_max/2, valeur mesurée ;
- une rentrée à ×77 est plafonnée à ×10 et détruit quand même l'étage.

### Task 4 : parachute

**Files:**
- Modify : `reentry.py` (`should_deploy`, `parachute_area`), `orbiter.py` (`parachute_progress` et traînée ajoutée), `tests/test_reentry.py`.

**Tests :**
- pas de déploiement au-dessus de l'altitude prévue, ni au-dessus de la vitesse max ;
- montée progressive de 0 à 1 sur 3 s ;
- le parachute n'est jamais rétracté ;
- le CM seul, lâché depuis une rentrée orbitale, se pose (l'engin n'est pas crashé) avec une vitesse finale mesurée sous 10 m/s.

### Task 5 : encart, plasma

**Files:**
- Create : `graphical/plasma.py`
- Modify : `graphical/rocket.py`
- Test : `tests/test_plasma.py`

**Fonctions :**
- `glow_color(q) -> (r, g, b, a)`, avec a = 0 sous 50 kW/m² ;
- `glow_polygons(bbox, q, t)`.

### Task 6 : encart, parachute

**Files:**
- Create : `graphical/parachute.py`
- Modify : `graphical/rocket.py`, où `state_key` inclut le parachute déployé (la pile est réduite pour faire de la place au-dessus)
- Test : `tests/test_parachute_view.py`

**Fonction :** `canopies(anchor, width, count, progress, t, room)`, qui renvoie la voilure en polygone et les suspentes.

### Task 7 : encart, désintégration

**Files:**
- Create : `graphical/breakup.py`
- Modify : `graphical/rocket.py`. `RocketView` garde l'engin affiché ; s'il est `destroyed`, l'encart joue la désintégration de son dernier dessin pendant 2,5 s, affiche « Détruit », puis passe au nouvel engin.
- Test : `tests/test_breakup.py`

**Fonctions :**
- `make_fragments(layout, ox, oy, seed)` ;
- `fragment_polygon(fragment, t)` ;
- `fragment_color(fragment, t)`.

### Task 8 : vérification dans l'appli

- Rejouer une rentrée du CM et une rentrée d'un étage dans l'appli, avec des captures d'écran.
- Mesurer les images par seconde.
- Lancer les 5 scénarios.
- Lancer toute la suite de tests.
