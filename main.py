import pygame
import sys
from grille import Grille

# CONSTANTES
LARGEUR_INIT, HAUTEUR_INIT = 900, 700
FPS = 60

# Couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
GRIS_CLAIR = (230, 230, 230)
GRIS_FONCE = (50, 50, 50)
BLEU_MENU = (50, 50, 150)
BOUTON_COULEUR = (100, 100, 200)
BOUTON_HOVER = (150, 150, 250)

# motifs connus
MOTIFS = {
    "Planeur": [(0, -1), (1, 0), (-1, 1), (0, 1), (1, 1)],
    "Vaisseau (LWSS)": [(1, -1), (4, -1), (0, 0), (0, 1), (4, 1), (0, 2), (1, 2), (2, 2), (3, 2)],
    "R-Pentomino": [(1, 0), (2, 0), (0, 1), (1, 1), (1, 2)],
    "Le Gland (Chaos)": [(1, 0), (3, 1), (0, 2), (1, 2), (4, 2), (5, 2), (6, 2)],
    "Ligne de 10": [(x, 0) for x in range(10)], # Génère une liste de coordonnées horizontales automatiquement
    "Canon de Gosper": [
        (0, 4), (0, 5), (1, 4), (1, 5), (10, 4), (10, 5), (10, 6), (11, 3), (11, 7),
        (12, 2), (12, 8), (13, 2), (13, 8), (14, 5), (15, 3), (15, 7), (16, 4), (16, 5),
        (16, 6), (17, 5), (20, 2), (20, 3), (20, 4), (21, 2), (21, 3), (21, 4), (22, 1),
        (22, 5), (24, 0), (24, 1), (24, 5), (24, 6), (34, 2), (34, 3), (35, 2), (35, 3)
    ]
}

# classe des boutons
class Bouton:
    def __init__(self, x, y, w, h, texte, action_callback):
        """
        Initialise un bouton avec sa position, sa taille, son texte et son action.
        Argument : x (int), y (int), w (largeur), h (hauteur), texte (str), action_callback (fonction)
        Return : None (Constructeur)
        """
        self.rect = pygame.Rect(x, y, w, h)
        self.texte = texte
        self.action = action_callback # Fonction à exécuter lors du clic
        self.survol = False

    def dessiner(self, screen, font):
        """
        Dessine le bouton et son texte sur l'écran donné.
        Argument : screen (Surface Pygame), font (Police Pygame)
        Return : None (Action d'affichage)
        """
        couleur = BOUTON_HOVER if self.survol else BOUTON_COULEUR
        pygame.draw.rect(screen, couleur, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLANC, self.rect, 2, border_radius=5)
        
        txt_surf = font.render(self.texte, True, BLANC)
        # Calcul savant pour centrer le texte parfaitement dans le rectangle
        tx = self.rect.centerx - txt_surf.get_width() // 2
        ty = self.rect.centery - txt_surf.get_height() // 2
        screen.blit(txt_surf, (tx, ty))

    def check_hover(self, mouse_pos):
        """
        Vérifie si la souris survole le bouton et met à jour l'état interne.
        Argument : mouse_pos (tuple x, y)
        Return : None
        """
        self.survol = self.rect.collidepoint(mouse_pos) # Retourne True si la souris est dans le rectangle

    def check_click(self, mouse_pos):
        """
        Déclenche l'action associée au bouton si la position donnée est à l'intérieur.
        Argument : mouse_pos (tuple x, y)
        Return : None
        """
        if self.rect.collidepoint(mouse_pos):
            self.action() # Exécute la fonction stockée dans self.action


# Classe du jeu
class Jeu:
    def __init__(self):
        """
        Initialise l'environnement Pygame, la fenêtre, les polices et les variables d'état du jeu.
        Argument : Aucun
        Return : None (Constructeur)
        """
        pygame.init()
        self.screen = pygame.display.set_mode((LARGEUR_INIT, HAUTEUR_INIT), pygame.RESIZABLE)
        pygame.display.set_caption("Jeu de la Vie")
        self.clock = pygame.time.Clock()
        
        # Polices
        self.font_ui = pygame.font.Font("assets/font.ttf", 18)
        self.font_menu = pygame.font.Font("assets/font.ttf", 16)
        self.font_titre = pygame.font.Font("assets/font.ttf", 18)
        self.font_info = pygame.font.SysFont("consolas", 14)
        
        self.grille = Grille()
        
        # États
        self.en_pause = True
        self.en_menu = False
        self.page_menu = "principal" # principal ou motifs
        self.dragging = False 
        self.is_fullscreen = False
        
        self.compteur_stagnation = 0
        self.SEUIL_STAGNATION = 10 
        
        self.taille_cellule = 20
        self.largeur_ecran = LARGEUR_INIT
        self.hauteur_ecran = HAUTEUR_INIT
        self.recentrer_camera()

        self.speed_level = 5 
        self.update_speed_delay() 
        self.dernier_update = 0

        self.boutons = []
        self.refresh_boutons() 

    def update_speed_delay(self):
        """
        Calcule le délai en millisecondes entre chaque génération basé sur le niveau de vitesse.
        Argument : Aucun
        Return : None (Met à jour self.vitesse_simulation)
        """
        # Plus speed_level est haut, plus le délai est court (donc ça va vite)
        self.vitesse_simulation = 120 - (self.speed_level * 10)

    def change_speed(self, delta):
        """
        Augmente ou diminue le niveau de vitesse et met à jour le délai.
        Argument : delta (int, positif ou négatif)
        Return : None
        """
        # Maintient la vitesse entre 0 et 10
        self.speed_level = max(0, min(10, self.speed_level + delta))
        self.update_speed_delay()

    # gestion menus et boutons
    def refresh_boutons(self):
        """
        Recharge la liste des boutons en fonction de la page de menu active (principal ou motifs).
        Argument : Aucun
        Return : None
        """
        if self.page_menu == "principal":
            self.charger_boutons_principal()
        elif self.page_menu == "motifs":
            self.charger_boutons_motifs()

    def changer_page(self, nom_page):
        """
        Change l'identifiant de la page courante et rafraîchit les boutons.
        Argument : nom_page (str)
        Return : None
        """
        self.page_menu = nom_page
        self.refresh_boutons()

    def charger_boutons_principal(self):
        """
        Crée et positionne les boutons pour le menu principal.
        Argument : Aucun
        Return : None (Remplit self.boutons)
        """
        cx = self.largeur_ecran // 2
        cy = self.hauteur_ecran // 2
        w, h = 220, 45
        
        self.boutons = [
            # Lambda permet de retarder l'appel de la fonction jusqu'au clic
            Bouton(cx - w - 10, cy - 40, w, h, "Figures Usuelles >", lambda: self.changer_page("motifs")),
            
            # Actions principales
            Bouton(cx - w - 10, cy + 20, w, h, "Effacer Grille", self.action_clear),
            
            # Vitesse
            Bouton(cx - 100, cy + 160, 40, 40, "-", lambda: self.change_speed(-1)),
            Bouton(cx + 60, cy + 160, 40, 40, "+", lambda: self.change_speed(1))
        ]

    def charger_boutons_motifs(self):
        """
        Crée et positionne les boutons pour la liste des motifs prédéfinis.
        Argument : Aucun
        Return : None (Remplit self.boutons)
        """
        cx = self.largeur_ecran // 2
        cy = self.hauteur_ecran // 2
        w, h = 240, 40
        
        self.boutons = []
        
        # Bouton Retour
        self.boutons.append(Bouton(cx - w//2, cy - 150, w, h, "< Retour Menu", lambda: self.changer_page("principal")))
        
        y_start = cy - 80
        for i, nom_motif in enumerate(MOTIFS.keys()):
            y_pos = y_start + (i * 50)
            # v=nom_motif force la sauvegarde de la valeur actuelle dans la boucle pour la lambda
            btn = Bouton(cx - w//2, y_pos, w, h, nom_motif, lambda v=nom_motif: self.action_load_motif(v))
            self.boutons.append(btn)

    # actions
    def action_clear(self):
        """
        Action déclenchée par le bouton 'Effacer Grille' : réinitialise le jeu et ferme le menu.
        Argument : Aucun
        Return : None
        """
        self.reset_jeu()
        self.en_menu = False # Ferme le menu

    def action_load_motif(self, nom_motif):
        """
        Charge un motif spécifique au centre de l'écran et lance la simulation.
        Argument : nom_motif (str, clé du dictionnaire MOTIFS)
        Return : None
        """
        cx_ecran = self.largeur_ecran // 2
        cy_ecran = self.hauteur_ecran // 2
        # Convertit le centre de l'écran en coordonnées de grille
        gx, gy = self.ecran_vers_grille(cx_ecran, cy_ecran)
        
        motif = MOTIFS[nom_motif]
        for (dx, dy) in motif:
            # Ajoute chaque point du motif par rapport au centre calculé (gx, gy)
            self.grille.cellules.add((gx + dx, gy + dy))
        
        self.en_menu = False # Ferme le menu et lance le jeu
        self.page_menu = "principal" 
        self.refresh_boutons()

    def recentrer_camera(self):
        """
        Réinitialise le zoom et les décalages (offset) pour centrer la vue.
        Argument : Aucun
        Return : None
        """
        self.taille_cellule = 20
        self.offset_x = self.largeur_ecran // 2
        self.offset_y = self.hauteur_ecran // 2

    def reset_jeu(self):
        """
        Vide la grille, remet les compteurs à zéro et met le jeu en pause.
        Argument : Aucun
        Return : None
        """
        self.grille.cellules = set()
        self.grille.generation = 0
        self.compteur_stagnation = 0
        self.en_pause = True
        self.recentrer_camera()

    def basculer_fullscreen(self):
        """
        Bascule entre le mode fenêtré et le mode plein écran.
        Argument : Aucun
        Return : None
        """
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            # (0, 0) demande à Pygame d'utiliser la résolution native de l'écran
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((LARGEUR_INIT, HAUTEUR_INIT), pygame.RESIZABLE)
        
        # Met à jour les dimensions stockées pour les calculs de centrage
        self.largeur_ecran, self.hauteur_ecran = self.screen.get_size()
        self.refresh_boutons() 

    # conversion
    def ecran_vers_grille(self, pixel_x, pixel_y):
        """
        Convertit des coordonnées pixel (écran) en coordonnées de grille (logique).
        Argument : pixel_x (int), pixel_y (int)
        Return : tuple (int, int) représentant les indices x, y de la grille
        """
        # On soustrait l'offset (caméra) et on divise par la taille de la cellule
        gx = (pixel_x - self.offset_x) // self.taille_cellule
        gy = (pixel_y - self.offset_y) // self.taille_cellule
        return int(gx), int(gy)

    def grille_vers_ecran(self, grille_x, grille_y):
        """
        Convertit des coordonnées de grille (logique) en coordonnées pixel (écran).
        Argument : grille_x (int), grille_y (int)
        Return : tuple (int, int) représentant les pixels x, y sur l'écran
        """
        # on multiplie par la taille et on ajoute l'offset
        px = (grille_x * self.taille_cellule) + self.offset_x
        py = (grille_y * self.taille_cellule) + self.offset_y
        return int(px), int(py)

    # event
    def gestion_evenements(self):
        """
        Gère la boucle des événements Pygame (clavier, souris, fermeture).
        Argument : Aucun
        Return : None
        """
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.VIDEORESIZE:
                if not self.is_fullscreen:
                    self.largeur_ecran, self.hauteur_ecran = event.w, event.h
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.refresh_boutons()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.en_menu = not self.en_menu
                    if self.en_menu: 
                        self.en_pause = True
                        self.page_menu = "principal" 
                        self.refresh_boutons()
                
                elif event.key == pygame.K_F11:
                    self.basculer_fullscreen()
                
                if not self.en_menu:
                    if event.key == pygame.K_SPACE:
                        self.en_pause = not self.en_pause
                        if not self.en_pause: self.compteur_stagnation = 0
                    elif event.key == pygame.K_c and self.en_pause:
                        self.reset_jeu()
                    elif event.key == pygame.K_r and self.en_pause:
                        self.recentrer_camera()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clic Gauche
                    if self.en_menu:
                        for btn in self.boutons:
                            btn.check_click((mx, my))
                    else:
                        if self.en_pause:
                            # Mode édition : on ajoute/supprime une cellule
                            gx, gy = self.ecran_vers_grille(mx, my)
                            self.grille.ajouter_ou_supprimer(gx, gy)
                        else:
                            # Mode lecture : on active le déplacement de caméra (drag)
                            self.dragging = True
                elif event.button == 4: # Molette haut (Zoom avant)
                    self.taille_cellule = min(100, self.taille_cellule + 2)
                elif event.button == 5: # Molette bas (Zoom arrière)
                    self.taille_cellule = max(4, self.taille_cellule - 2)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: self.dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.en_menu:
                    for btn in self.boutons:
                        btn.check_hover((mx, my))
                elif self.dragging and not self.en_pause:
                    dx, dy = event.rel # Récupère le déplacement relatif depuis la dernière frame
                    self.offset_x += dx
                    self.offset_y += dy

    def update(self):
        """
        Met à jour la logique du jeu : fait évoluer la grille si le temps est écoulé et gère la stagnation.
        Argument : Aucun
        Return : None
        """
        if not self.en_pause and not self.en_menu:
            maintenant = pygame.time.get_ticks()
            # Système de délai pour contrôler la vitesse indépendamment des FPS
            if maintenant - self.dernier_update > self.vitesse_simulation:
                a_bouge = self.grille.evoluer()
                self.dernier_update = maintenant
                if not a_bouge:
                    self.compteur_stagnation += 1
                    if self.compteur_stagnation >= self.SEUIL_STAGNATION:
                        self.reset_jeu() # Reset automatique si plus rien ne bouge
                else:
                    self.compteur_stagnation = 0

    # affichage
    def dessiner_grillage(self):
        """
        Dessine les lignes verticales et horizontales de la grille visibles à l'écran.
        Argument : Aucun
        Return : None
        """
        # calcule uniquement les lignes visibles à l'écran pour économiser des ressources
        start_col = -self.offset_x // self.taille_cellule
        end_col = start_col + (self.largeur_ecran // self.taille_cellule) + 2
        start_row = -self.offset_y // self.taille_cellule
        end_row = start_row + (self.hauteur_ecran // self.taille_cellule) + 2

        for c in range(int(start_col), int(end_col)):
            x = (c * self.taille_cellule) + self.offset_x
            pygame.draw.line(self.screen, GRIS_CLAIR, (x, 0), (x, self.hauteur_ecran))
        for r in range(int(start_row), int(end_row)):
            y = (r * self.taille_cellule) + self.offset_y
            pygame.draw.line(self.screen, GRIS_CLAIR, (0, y), (self.largeur_ecran, y))

    def afficher_hud(self):
        """
        Affiche les informations textuelles (Génération, Vitesse, Touches) en superposition.
        Argument : Aucun
        Return : None
        """
        info_gen = f"Génération: {self.grille.generation}"
        if self.compteur_stagnation > 0:
            info_gen += f" | Stagnation: {self.compteur_stagnation}/{self.SEUIL_STAGNATION}"
        
        txt_gen = self.font_ui.render(info_gen, True, NOIR)
        # Positionne le texte en haut à droite avec une marge de 10px
        self.screen.blit(txt_gen, (self.largeur_ecran - txt_gen.get_width() - 10, 10))

        txt_speed = self.font_ui.render(f"Vitesse: {self.speed_level}/10", True, GRIS_FONCE)
        self.screen.blit(txt_speed, (self.largeur_ecran - txt_speed.get_width() - 10, 30))

        txt = self.font_ui.render("ECHAP : MENU & OPTIONS", True, GRIS_FONCE)
        self.screen.blit(txt, (10, 10))

    def afficher_menu(self):
        """
        Dessine l'interface du menu (fond semi-transparent, cadre, titre, boutons, instructions).
        Argument : Aucun
        Return : None
        """
        s = pygame.Surface((self.largeur_ecran, self.hauteur_ecran))
        s.set_alpha(220) # Définit la transparence
        s.fill(BLANC)
        self.screen.blit(s, (0,0))

        cx = self.largeur_ecran // 2
        cy = self.hauteur_ecran // 2

        # Cadre
        rect_menu = pygame.Rect(cx - 250, cy - 250, 500, 500)
        pygame.draw.rect(self.screen, BLEU_MENU, rect_menu, border_radius=15)
        pygame.draw.rect(self.screen, NOIR, rect_menu, 3, border_radius=15)

        # Titre selon la page
        titre_txt = "MENU PRINCIPAL" if self.page_menu == "principal" else "FIGURES USUELLES"
        titre = self.font_titre.render(titre_txt, True, BLANC)
        self.screen.blit(titre, (cx - titre.get_width()//2, rect_menu.y + 20))

        # dessin des boutons
        for btn in self.boutons:
            btn.dessiner(self.screen, self.font_menu)

        # page principale
        if self.page_menu == "principal":
            # Indicateurs Vitesse
            txt_vit = self.font_menu.render(f"Vitesse: {self.speed_level}", True, BLANC)
            txt_ms = self.font_ui.render(f"({self.vitesse_simulation} ms)", True, GRIS_CLAIR)
            self.screen.blit(txt_vit, (cx - txt_vit.get_width()//2, cy + 160))
            self.screen.blit(txt_ms, (cx - txt_ms.get_width()//2, cy + 185))

            # Liste des touches (Commandes)
            x_keys = cx + 10
            y_keys = cy - 80
            pygame.draw.line(self.screen, BLANC, (cx, cy - 90), (cx, cy + 130), 2) 

            commandes = [
                ("SOURIS G", "Dessiner / Bouger"),
                ("MOLETTE", "Zoomer / Dézoomer"),
                ("ESPACE", "Lecture / Pause"),
                ("C", "Vider la grille"),
                ("R", "Recentrer Caméra"),
                ("F11", "Plein Écran"),
                ("ECHAP", "Menu")
            ]

            for i, (touche, desc) in enumerate(commandes):
                txt_t = self.font_info.render(f"[{touche}]", True, (255, 255, 100))
                txt_d = self.font_info.render(desc, True, BLANC)
                self.screen.blit(txt_t, (x_keys + 10, y_keys + i*28))
                self.screen.blit(txt_d, (x_keys + 100, y_keys + i*28))

    def afficher(self):
        """
        Orchestre l'affichage complet : fond, grille, cellules vivantes, HUD et menus.
        Argument : Aucun
        Return : None
        """
        self.screen.fill(BLANC)
        self.dessiner_grillage()

        for (gx, gy) in self.grille.cellules:
            px, py = self.grille_vers_ecran(gx, gy)
            # Ne dessine pas les cellules qui sont hors de l'écran (culling)
            if px < -self.taille_cellule or px > self.largeur_ecran or py < -self.taille_cellule or py > self.hauteur_ecran:
                continue
            rect = pygame.Rect(px + 1, py + 1, self.taille_cellule - 1, self.taille_cellule - 1)
            pygame.draw.rect(self.screen, NOIR, rect)

        self.afficher_hud()
        if self.en_menu: self.afficher_menu()

        pygame.display.flip()

    def run(self):
        """
        Boucle principale du programme qui maintient le jeu en vie jusqu'à la fermeture.
        Argument : Aucun
        Return : None
        """
        while True:
            self.gestion_evenements()
            self.update()
            self.afficher()
            self.clock.tick(FPS)

if __name__ == "__main__":
    jeu = Jeu()
    jeu.run()