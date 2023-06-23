# Traitement des adresses du Répertoire Électoral Unique

Vous trouverez ici à titre informatif l'ensemble des codes de traitement sur les données du REU ayant permis la diffusion des adresses et bureaux de vote du fichier, ainsi que la documentation associée. Ce travail a été réalisé par l'Insee entre octobre 2022 et juin 2023 avec le soutien d'Etalab. Pour plus de détails, vous pouvez consulter la page méthodologique ici : ```doc/methodologie.html```.

## Les données

Les données brutes correspondent à une extraction des adresses du Répertoire Électoral Unique réalisée en septembre 2022. Le travail réalisé permet la diffusion de 2 fichiers :

- La table des adresses normalisées et géolocalisées du REU
    + Dictionnaire des variables : ```doc/dictionnaire_donnees_adresses.html```
- La table des bureaux de vote du REU
    + Dictionnaire des variables : ```doc/dictionnaire_donnees_bv.html```

## La documentation

Quatre fichiers de documentation sont disponibles dans le dossier _doc_ :
- Le dictionnaire des variables de la table des adresses
- Le dictionnaire des variables de la table des bureaux de vote
- Un document méthodologique détaillant le travail effectué sur les données du REU
- Un document présentant l'architecture des scripts du dossier _src_ à des fins de reproductibilité

## Les codes

Le dossier _src_ rassemble l'ensemble des scripts ayant permis la diffusion des adresses et bureaux de vote du REU.
Pour plus de détails sur l'articulation des fichiers et leur rôle, vous pouvez consulter la page consacrée à la reproductibilité du projet : ```doc/reproductibilite.html```.
