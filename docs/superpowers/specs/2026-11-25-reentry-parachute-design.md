# Rentrée atmosphérique : destruction, bouclier, parachute — conception

## Intention

Rendre la rentrée atmosphérique dangereuse et visible :
- un engin sans bouclier thermique qui rentre trop vite est détruit ;
- une capsule avec bouclier survit, et son parachute se déploie tout seul pour qu'elle se pose ;
- l'encart de la fusée montre la scène : plasma pendant la rentrée, désintégration de l'engin, ouverture du parachute.

L'objectif est autant le réalisme que le côté sympa de la simulation.

## Non-objectifs

- Pas de modèle thermique fin : pas de matériaux, pas d'ablation, pas d'attitude.
- Pas de rupture mécanique due à la pression dynamique : seule la chaleur détruit.
- Pas de parachute qui se déchire : si l'engin va trop vite, le déploiement attend.
- Pas d'animation de rentrée sur la vue principale : l'animation est réservée à l'encart.

## Anti-objectifs

L'ajout serait un échec, même s'il marche techniquement, dans ces cas :
- **Une montée nominale détruit un lanceur.** Saturn V, Ariane 5 et M51 doivent survivre à leur ascension.
- **La rentrée devient invisible en temps accéléré.** Aujourd'hui, au-delà de ×10, le calcul orbital ignore l'atmosphère.
- **On perd la fluidité.** La cible est de rester au-dessus de 55 images/s, mesuré.

## Approches envisagées

1. **Flux thermique accumulé (choisie).**
   - On calcule le flux au point d'arrêt, avec la formule de Sutton-Graves : q̇ = 1,7415e-4 · √(ρ/Rn) · v³ en W/m².
   - Ce flux s'accumule en une charge Q, avec un refroidissement exponentiel.
   - L'engin est détruit quand Q dépasse un seuil.
   - C'est physiquement fondé, et ça distingue une montée (rapide mais brève, en air peu dense) d'une rentrée.
2. **Seuil de vitesse et d'altitude.** Plus simple, mais arbitraire : une montée rapide le déclencherait, et ça ne réagit pas à l'angle de rentrée.
3. **Seuil de pression dynamique.** Ça modélise la rupture mécanique, pas la chaleur. Le mélanger avec le flux compliquerait le calibrage. Écarté.

## Conception

### Équipement des pièces (fichiers .rocket)

Une nouvelle section, optionnelle, par pièce : `[equipment.<pièce>]`. Elle est lue sans tenir compte de la casse, comme `[shape.*]`.

```
[equipment.cm]
heat_shield = yes
parachute = 25.4, 3, 3000, 200   ; diamètre (m), nombre, altitude de déploiement (m), vitesse max de déploiement (m/s)
```

Une valeur invalide garde la valeur par défaut et affiche un message, comme pour `shape`. Par défaut, une pièce n'a ni bouclier ni parachute.

### Séparation du CSM (choix de l'utilisateur : option a)

`saturne5.rocket` et `saturne5_moon.rocket` remplacent la pièce `CSM` par deux pièces dans le même étage :
- **SM** : moteur et carburant, dessiné sans pointe ;
- **CM** : sans moteur, avec la pointe `capsule_les`, `heat_shield`, et `parachute = 25.4, 3, 3000, 200`.

Les masses gardent le total actuel, pour que le delta-v et les missions existantes ne changent pas :

| Fichier | SM (sec / carburant) | CM (sec / carburant) | Total |
|---|---|---|---|
| saturne5.rocket | 3 000 kg / 21 500 kg | 5 500 kg / 0 | 30 000 kg |
| saturne5_moon.rocket | 3 000 kg / 6 300 kg | 5 500 kg / 0 | 14 800 kg |

La traînée de 30 est répartie : 15 pour le SM, 15 pour le CM.

**Nouvelle règle de séparation.** Quand on largue un étage, les pièces **centrales** (`position = center`) de cet étage partent ensemble, en un seul engin empilé : la première pièce listée devient l'étage 0, la suivante l'étage 1. Les pièces **latérales** (boosters) restent séparées une par une, comme aujourd'hui.
- Pour Apollo, larguer l'étage CSM donne un engin « SM+CM », puis « larguer » sur celui-ci sépare le SM du CM.
- Ariane 5 n'est pas affectée : son étage 1 n'a qu'une pièce centrale (EPC) plus des boosters latéraux.

Le test `test_rocket_files` et l'ordre de dessin (`draw_below = csm` → `cm`) sont mis à jour.

### Échauffement et destruction (physique)

- **Calcul** : q̇ = 1,7415e-4 · √(ρ/Rn) · v³, où :
  - Rn est le rayon de la pièce du bas de la pile (diamètre/2 de sa forme) ;
  - v est la vitesse inertielle, car le simulateur ne fait pas tourner l'atmosphère.
- **Accumulation** : la charge Q se met à jour par Q ← Q·e^(−dt/τ) + q̇·dt. Le refroidissement empêche qu'une longue montée accumule de la chaleur.
- **Destruction** : un engin **sans aucune pièce à bouclier** est détruit quand Q > Q_max.
  - Il est retiré comme un crash. L'événement est distinct (« détruit à la rentrée ») et s'affiche dans la console.
  - Un engin qui a au moins une pièce à bouclier n'est jamais détruit par la chaleur. C'est une approximation : un SM encore attaché au CM survit.
- **Calibrage** : τ et Q_max seront calibrés et mesurés pendant l'implémentation.
  - Cible : un étage nu qui rentre depuis l'orbite basse (environ 7,8 km/s) se désintègre entre 70 et 85 km.
  - Les montées nominales de Saturn V, d'Ariane 5 (avec sa mission) et de M51 doivent garder une marge d'au moins ×2 sous Q_max.
- **Temps accéléré** : un engin en mouvement dans une atmosphère dont la densité est non nulle est toujours calculé pas à pas. L'accélération est alors plafonnée à ×10, comme pour un moteur allumé.
  - Un engin posé, de vitesse nulle, ne plafonne rien.
  - Une rentrée observée à ×77 est donc ralentie à ×10 pendant la traversée.

### Parachute (physique)

- **Déploiement automatique** : il se déclenche dès que toutes ces conditions sont réunies :
  - l'engin a un parachute ;
  - l'attracteur a une atmosphère ;
  - l'altitude est sous l'altitude de déploiement ;
  - l'engin descend ;
  - la vitesse est sous la vitesse maximale de déploiement.
- **Pas de retour en arrière** : une fois déployé, le parachute le reste.
- **Traînée ajoutée** : 0,8 × nombre × π(d/2)², montée progressivement sur 3 s.
- **Vérification attendue** : avec le CM à 5 500 kg, la vitesse limite est d'environ 8 m/s au sol, donc sous les 10 m/s du crash. Elle sera mesurée dans un test.
- **Après le parachute** : l'atterrissage existant (moins de 10 m/s) pose l'engin.

### Animation dans l'encart

Elle s'applique à l'engin contrôlé seulement.

- **Plasma** : un halo autour de l'engin dès que q̇ dépasse 50 kW/m², plus fort sur le bas, qui fait face au vent.
  - Couleur : du rouge sombre vers l'orange, puis le blanc, selon q̇.
  - Le halo scintille, avec la même technique que les flammes.
  - Il s'affiche que l'engin ait un bouclier ou non.
- **Destruction** :
  - les pièces du dernier dessin sont découpées en fragments qui s'écartent en tournant, rougeoient, puis s'éteignent en environ 2,5 s, avec quelques étincelles ;
  - « Détruit » s'affiche ;
  - ensuite, l'encart passe à l'engin qui devient le contrôlé.
- **Parachute** :
  - suspentes et voilures au-dessus de la capsule ;
  - les voilures s'ouvrent de 0 à 1 sur les 3 s du déploiement (ellipse aplatie, puis dôme) ;
  - un léger balancement suit.
- **Performance** : mêmes règles que les flammes. On réutilise les maillages, et on ne redessine pas la fusée à chaque image. Le coût sera mesuré.

## Laissé à l'implémentation

- Les valeurs exactes de τ et Q_max, à condition de respecter le calibrage ci-dessus.
- Les longueurs de dessin du SM et du CM, pour que la silhouette du CSM reste la même qu'aujourd'hui.
- Le nombre de fragments et le style exact des étincelles et du halo.
