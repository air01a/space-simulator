# Encart « état de la fusée » — conception

Date : 2026-11-25

## Intention

Afficher en bas à droite de l'écran un dessin 2D de profil de l'engin piloté, mis à
jour en direct selon son état. Deux objectifs, donnés par l'utilisateur :

1. **Voir l'état de la fusée** pendant le pilotage : quels étages restent, lequel
   brûle, combien de carburant il reste, ce qui a été largué.
2. **Rendre la simulation plus sympa** visuellement.

Pas de photoréalisme : un dessin propre, aux proportions et couleurs réalistes des
vrais lanceurs.

## Objectifs

- Silhouette de l'engin piloté, construite à partir de ses étages et pièces
  (`Stages` / `Stage_Composant` dans `orbiter.py`).
- Mise à jour en direct :
  - **séparation** : une pièce/un étage largué disparaît du dessin ;
  - **carburant** : chaque réservoir montre son niveau ;
  - **étage actif** (étage 0, moteur allumé, carburant > 0) mis en évidence ;
  - **pièce vide** (dans `stages.empty_part`) grisée.
- Changer d'engin piloté (bouton Control, ex : un booster largué) affiche cet engin.
- Fusées fournies dessinées avec leurs dimensions réelles : Ariane 5, Saturn V
  (Apollo), LEM (`saturne5_moon.rocket`), satellite.

## Non-objectifs (pour cette version)

- Animation des flammes : prévue plus tard par l'utilisateur. La conception doit
  la rendre facile (position et état des tuyères disponibles), mais on ne la fait pas.
- Animation de la séparation (étage qui s'éloigne).
- Photoréalisme, images bitmap.
- Orientation de la fusée dans l'encart : toujours dessinée verticale, coiffe en haut.

## Anti-objectifs (ce qui serait un échec même si ça marche)

- Faire baisser la fluidité : la simulation tient aujourd'hui 60 images/s avec
  ~3 ms de calcul par image ; l'encart doit coûter < 0,5 ms par image.
- Casser une fusée qui n'a pas de description de forme (fichiers `.rocket`
  existants ou futurs) : elle doit s'afficher avec une forme par défaut.
- Nouvelle dépendance (tout se fait avec Kivy, déjà utilisé).

## Approches envisagées

| | Approche | Pour | Contre |
|---|---|---|---|
| **A (retenue)** | Dessin vectoriel Kivy à partir d'une description de forme par pièce | Entièrement dynamique (carburant, étage actif, séparation) ; flammes faciles à ajouter ; pas d'images à maintenir | Style « schéma soigné » plutôt qu'illustration détaillée |
| B | Une image PNG par pièce, empilées | Plus de détail, l'utilisateur peut fournir ses dessins | Images à produire pour chaque fusée ; carburant et flammes à superposer à part |
| C | Fichiers SVG chargés par Kivy | Détail + éditable (Inkscape) | Support SVG de Kivy limité (dégradés), couleurs dynamiques malcommodes |

**Choix de l'utilisateur : A**, parce qu'elle sert le mieux ses deux objectifs
(état en direct, flammes animées à venir).

## Conception

### 1. Description des formes dans les fichiers `.rocket`

Une section optionnelle par pièce, nommée `shape.<nom de la pièce>` (nom en
minuscules, comme `configparser` le renvoie déjà : `s-ic`, `booster1`…).
Unités : mètres.

```ini
[shape.epc]
length = 30.5        ; longueur du corps (m)
diameter = 5.4       ; diamètre (m)
top = none           ; forme du haut : none | ogive | cone | fairing | capsule
nozzles = 1          ; nombre de tuyères dessinées sous la pièce (0 = aucune)
color = #f0f0f0      ; couleur du corps
band = #202020       ; optionnel : couleur des bandes décoratives
position = center    ; center = empilé dans l'axe | side = booster latéral
```

Deux clés supplémentaires pour une silhouette réaliste quand l'ordre des étages
de la simulation ne correspond pas à la vraie disposition (cas d'Apollo, où le
LEM est logé sous le CSM alors qu'il est largué après lui) :

```ini
draw_below = csm     ; dessiner cette pièce juste sous la pièce « csm »,
                     ; quel que soit son étage
enclosed = true      ; pièce logée dans un carénage (adaptateur) : on dessine
                     ; le carénage translucide, la pièce reste visible dedans
```

- `draw_below` ne change **que le dessin** : l'ordre de largage reste celui des
  étages. Plusieurs pièces avec le même `draw_below` gardent l'ordre du fichier
  (la première juste sous la cible).
- `enclosed` : le carénage est un tronc de cône allant du diamètre de la pièce
  dessinée en dessous au diamètre de la cible. Il disparaît quand il ne reste
  plus de pièce `enclosed` dedans.
- Si la cible de `draw_below` n'existe plus (déjà larguée), la pièce reprend sa
  place normale dans la pile.
- Le haut `top = capsule_les` dessine une capsule avec sa tour de sauvetage.

- Toutes les clés sont optionnelles. Valeurs par défaut (forme générique) :
  `length = 10`, `diameter = 3`, `top = none` (`fairing` si la pièce est
  `payload`), `nozzles = 1` (0 pour `payload`), `color = #d0d0d0`, pas de bande,
  `position = center`.
- Une pièce sans section `shape.*` utilise ces valeurs par défaut.
- La forme est lue au chargement (`Load_Orbiters.get_orbiter`) et **stockée dans
  le `Stage_Composant`** (attribut `shape`). Elle suit donc la pièce partout :
  séparation (`separate_stage` crée un nouvel engin avec la même pièce), amarrage
  (`dock` recopie les pièces).
- `Stage_Composant` garde aussi sa masse de carburant initiale
  (`initial_carburant_mass`) pour calculer le niveau.

### 2. Mise en page (fonction pure, testable sans Kivy)

Module `graphical/rocket_layout.py`, fonction
`layout_rocket(stages, width, height) -> RocketLayout`.

- **Empilement** : `stages.stages[0]` (le premier étage à brûler) en bas, puis
  chaque étage suivant au-dessus. Dans un étage, les pièces `center` sont
  empilées dans l'axe, dans l'ordre du fichier.
- **Boosters** (`side`) : répartis de part et d'autre du corps central de leur
  étage, alternativement à gauche et à droite, base alignée sur la base de
  l'étage.
- **Échelle** : la fusée entière est mise à l'échelle pour tenir dans l'encart
  (en gardant les proportions) avec une marge. Quand un étage est largué, la fusée
  restante est redimensionnée pour remplir l'encart (effet de « zoom » voulu :
  un satellite seul reste lisible).
- Le résultat décrit des formes en pixels de l'encart : pour chaque pièce, son
  rectangle de corps, son haut (ogive/coiffe…), ses tuyères (positions exposées
  pour les futures flammes), son niveau de carburant (0–1) et son état
  (`active`, `empty`, `idle`).

### 3. Dessin (widget Kivy)

Module `graphical/rocket.py`, widget `RocketView`.

- Placé en bas à droite, au-dessus du bandeau d'informations, dans
  `spacesimulator.kv` et `spacesimulator_small.kv`. Taille proportionnelle à la
  hauteur de la fenêtre (≈ 300 × 450 px pour 1920 × 1200).
- Fond sombre semi-transparent avec un bord fin, nom de l'engin en haut.
- Pour chaque pièce :
  - corps : couleur `color`, ombrage simple (bande plus claire à gauche, plus
    sombre à droite) pour donner du volume ;
  - bandes décoratives si `band` ;
  - niveau de carburant : remplissage plus sombre de bas en haut à l'intérieur
    du corps, proportionnel au niveau ;
  - état : `active` = contour lumineux ; `empty` = couleurs désaturées ;
  - haut et tuyères dessinés selon `top` et `nozzles`.
- Pourcentage de carburant écrit à côté des pièces de l'étage actif.
- `Graphics.draw` (`display.py`) appelle `RocketView.update(orbiter_courant)` à
  chaque image. Le widget **ne redessine que si l'état a changé** (ensemble des
  pièces, niveaux arrondis au %, états, taille de l'encart), pour rester sous
  0,5 ms par image.
- Aucun engin piloté : encart vide avec « None ».

### 4. Fusées fournies

Dimensions réelles approximatives à renseigner (m) :

| Fusée | Pièce | Longueur | Diamètre | Particularités |
|---|---|---|---|---|
| Ariane 5 | booster1/2 (EAP) | 31 | 3 | side, ogive, 1 tuyère, blanc |
| | epc | 30.5 | 5.4 | center, 1 tuyère (Vulcain), blanc |
| | eps | 3.4 | 5.4 | center, 1 tuyère |
| | payload | 17 | 5.4 | coiffe |
| Saturn V | s-ic | 42 | 10 | 5 tuyères, blanc + bandes noires |
| | s-ii | 24.9 | 10 | 5 tuyères, blanc |
| | s-ivb | 17.8 | 6.6 | 1 tuyère, blanc + bandes noires |
| | csm | 11 | 3.9 | `capsule_les` (capsule + tour de sauvetage), 1 tuyère |
| | lem_descent | 3.2 | 4.2 | doré, 1 tuyère, `draw_below = csm`, `enclosed` |
| | lem_ascent | 2.8 | 4.0 | gris, 1 tuyère, `draw_below = csm`, `enclosed` |
| LEM (`saturne5_moon`) | csm, lem_descent, lem_ascent | idem | idem | idem |
| Satellite | payload | 3 | 2 | gris/doré |

**Silhouette réaliste d'Apollo (choix de l'utilisateur)** : le LEM est dessiné
sous le CSM, dans l'adaptateur (SLA) translucide, et non au sommet comme l'ordre
des étages le placerait. Ordre de dessin de bas en haut : S-IC, S-II, S-IVB,
[SLA : LEM descente, LEM remontée], CSM + tour de sauvetage.

Note : dans `saturne5_moon.rocket`, le CSM est l'étage 1 ; une fois le CSM
largué, le LEM reprend sa place normale (règle « cible disparue » ci-dessus).

## Tests

- `layout_rocket` (sans Kivy) : empilement dans l'ordre des étages, boosters de
  part et d'autre, mise à l'échelle dans l'encart, pièce sans forme → défaut,
  niveau de carburant, états, rendu après `sep_part` et après `dock`,
  `draw_below` (LEM sous le CSM, ordre conservé, cible larguée → place normale),
  carénage `enclosed` présent puis absent.
- Chargement des fichiers `.rocket` : les formes sont lues ; un fichier sans
  section `shape.*` se charge comme avant.
- Dans l'appli : capture d'écran de l'encart pour Ariane 5 (complet, après
  largage des boosters, après largage de l'EPC) et Saturn V ; mesure du coût par
  image (< 0,5 ms).

## Décisions prises par Claude (à contester si besoin)

- Format de description : sections `shape.<pièce>` dans le fichier `.rocket`
  existant plutôt qu'un fichier séparé (tout ce qui décrit une fusée reste au
  même endroit).
- Remise à l'échelle après largage (effet de zoom) plutôt qu'une échelle fixe.
- Étage actif = étage 0 quand le moteur est allumé et qu'il reste du carburant.
- Pourcentage de carburant affiché seulement pour l'étage actif (lisibilité).
- Couleurs et dimensions des fusées fournies : valeurs publiques approximatives.

## Laissé au développeur

- Rendu exact des ombrages, épaisseur des traits, police.
- Détails de forme de chaque `top` (proportions de l'ogive, de la coiffe).
