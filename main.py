import pygame
import sys
from grille import Grille

# --- CONSTANTES & CONFIGURATION ---
LARGEUR_INIT, HAUTEUR_INIT = 900, 700 
FPS = 60

# Palette de couleurs (R, V, B)
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
GRIS_CLAIR = (230, 230, 230)
GRIS_FONCE = (50, 50, 50)
ROUGE = (200, 50, 50)     # Pour l'état PAUSE
VERT = (50, 200, 50)      # Pour l'état LECTURE
BLEU_MENU = (50, 50, 150) # Fond des fenêtres
BOUTON_COULEUR = (100, 100, 200)
BOUTON_HOVER = (150, 150, 250)

# --- BANQUE DE MOTIFS ---
# Coordonnées relatives (dx, dy) pour dessiner des formes connues
MOTIFS = {
    "Planeur": [(0, -1), (1, 0), (-1, 1), (0, 1), (1, 1)],
    "Vaisseau (LWSS)": [(1, -1), (4, -1), (0, 0), (0, 1), (4, 1), (0, 2), (1, 2), (2, 2), (3, 2)],
    "Canon de Gosper": [
        (0, 4), (0, 5), (1, 4), (1, 5), (10, 4), (10, 5), (10, 6), (11, 3), (11, 7),
        (12, 2), (12, 8), (13, 2), (13, 8), (14, 5), (15, 3), (15, 7), (16, 4), (16, 5),
        (16, 6), (17, 5), (20, 2), (20, 3), (20, 4), (21, 2), (21, 3), (21, 4), (22, 1),
        (22, 5), (24, 0), (24, 1), (24, 5), (24, 6), (34, 2), (34, 3), (35, 2), (35, 3)
    ]
}

class Bouton:
    """Classe utilitaire pour gérer les interactions UI simples (Hover/Clic)"""
    def __init__(self, x, y, w, h, texte, action_callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.texte = texte
        self.action = action_callback # La fonction à lancer au clic
        self.survol = False

    def dessiner(self, screen, font):
        # Changement de couleur si survolé
        couleur = BOUTON_HOVER if self.survol else BOUTON_COULEUR
        pygame.draw.rect(screen, couleur, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLANC, self.rect, 2, border_radius=5) # Bordure
        
        # Centrage du texte
        txt_surf = font.render(self.texte, True, BLANC)
        tx = self.rect.centerx - txt_surf.get_width() // 2
        ty = self.rect.centery - txt_surf.get_height() // 2
        screen.blit(txt_surf, (tx, ty))

    def check_hover(self, mouse_pos):
        """Met à jour l'état de survol"""
        self.survol = self.rect.collidepoint(mouse_pos)

    def check_click(self, mouse_pos):
        """Exécute l'action si le clic est dans le bouton"""
        if self.rect.collidepoint(mouse_pos):
            self.action()

class Jeu:
    """Contrôleur principal : Interface, Événements et Boucle de jeu"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((LARGEUR_INIT, HAUTEUR_INIT), pygame.RESIZABLE)
        pygame.display.set_caption("Jeu de la Vie")
        logo = pygame.image.load("assets/logo.png")
        pygame.display.set_icon(logo)
        self.clock = pygame.time.Clock()
        
        # Chargement des polices système
        self.font_ui = pygame.font.Font("assets/font.ttf", 18)
        self.font_menu = pygame.font.Font("assets/font.ttf", 14)
        self.font_titre = pygame.font.Font("assets/font.ttf", 16)
        self.font_info = pygame.font.SysFont("consolas", 14) 
        
        self.grille = Grille() # Logique métier
        
        # États du système
        self.en_pause = True
        self.en_menu = False
        self.dragging = False      # Pour le déplacement caméra (drag & drop)
        self.is_fullscreen = False
        
        # Détection de boucle infinie / monde stable
        self.compteur_stagnation = 0
        self.SEUIL_STAGNATION = 10 
        
        # Paramètres Caméra (Viewport)
        self.taille_cellule = 20
        self.largeur_ecran = LARGEUR_INIT
        self.hauteur_ecran = HAUTEUR_INIT
        self.recentrer_camera() # Initialise offset et zoom

        # Gestion du temps (Vitesse simulation variable)
        self.speed_level = 5 
        self.update_speed_delay() 
        self.dernier_update = 0

        # UI
        self.boutons = []
        self.init_boutons()

    def update_speed_delay(self):
        """Convertit le niveau 0-10 en délai millisecondes (Mapping linéaire inverse)"""
        self.vitesse_simulation = 120 - (self.speed_level * 10)

    def change_speed(self, delta):
        """Incrémente/Décrémente la vitesse avec bornage [0, 10]"""
        self.speed_level = max(0, min(10, self.speed_level + delta))
        self.update_speed_delay()

    def init_boutons(self):
        """Crée ou recrée les boutons (nécessaire lors du redimensionnement fenêtre)"""
        cx = self.largeur_ecran // 2
        cy = self.hauteur_ecran // 2
        w, h = 220, 40
        
        # Utilisation de lambdas pour passer des arguments aux callbacks
        self.boutons = [
            Bouton(cx - w - 10, cy - 80, w, h, "Effacer Grille", self.action_clear),
            Bouton(cx - w - 10, cy - 20, w, h, "Ajouter Planeur", lambda: self.action_load_motif("Planeur")),
            Bouton(cx - w - 10, cy + 40, w, h, "Ajouter Vaisseau", lambda: self.action_load_motif("Vaisseau (LWSS)")),
            Bouton(cx - w - 10, cy + 100, w, h, "Ajouter Canon Gosper", lambda: self.action_load_motif("Canon de Gosper")),
            
            Bouton(cx - 100, cy + 160, 40, 40, "-", lambda: self.change_speed(-1)),
            Bouton(cx + 60, cy + 160, 40, 40, "+", lambda: self.change_speed(1))
        ]

    # --- LOGIQUE MÉTIER (ACTIONS) ---
    def action_clear(self):
        self.reset_jeu()
        self.en_menu = False

    def action_load_motif(self, nom_motif):
        """Charge un motif au centre de la vue actuelle"""
        cx_ecran = self.largeur_ecran // 2
        cy_ecran = self.hauteur_ecran // 2
        gx, gy = self.ecran_vers_grille(cx_ecran, cy_ecran)
        
        motif = MOTIFS[nom_motif]
        for (dx, dy) in motif:
            self.grille.cellules.add((gx + dx, gy + dy))
        self.en_menu = False

    def recentrer_camera(self):
        """Remet la caméra à zéro (Centre écran = (0,0) Grille) et Reset Zoom"""
        self.taille_cellule = 20 
        self.offset_x = self.largeur_ecran // 2
        self.offset_y = self.hauteur_ecran // 2

    def reset_jeu(self):
        """Remise à zéro complète (Grille, Temps, Caméra)"""
        self.grille.cellules = set()
        self.grille.generation = 0
        self.compteur_stagnation = 0
        self.en_pause = True
        self.recentrer_camera()

    def basculer_fullscreen(self):
        """Gestion bascule Fenêtré <-> Plein Écran"""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((LARGEUR_INIT, HAUTEUR_INIT), pygame.RESIZABLE)
        
        # Important : Mettre à jour les dimensions connues pour le rendu
        self.largeur_ecran, self.hauteur_ecran = self.screen.get_size()
        self.init_boutons() # Recalcul positions boutons

    # --- CHANGEMENT DE REPÈRE (Affine) ---
    def ecran_vers_grille(self, pixel_x, pixel_y):
        """Transformée Inverse : Écran -> Monde"""
        gx = (pixel_x - self.offset_x) // self.taille_cellule
        gy = (pixel_y - self.offset_y) // self.taille_cellule
        return int(gx), int(gy)

    def grille_vers_ecran(self, grille_x, grille_y):
        """Projection : Monde -> Écran"""
        px = (grille_x * self.taille_cellule) + self.offset_x
        py = (grille_y * self.taille_cellule) + self.offset_y
        return int(px), int(py)

    # --- GESTION DES ENTRÉES (INPUT) ---
    def gestion_evenements(self):
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Redimensionnement fenêtre dynamique
            elif event.type == pygame.VIDEORESIZE:
                if not self.is_fullscreen:
                    self.largeur_ecran, self.hauteur_ecran = event.w, event.h
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.init_boutons()

            # --- CLAVIER ---
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.en_menu = not self.en_menu
                    if self.en_menu: self.en_pause = True # Auto-pause
                
                elif event.key == pygame.K_F11:
                    self.basculer_fullscreen()
                
                # Raccourcis actifs uniquement hors menu
                if not self.en_menu:
                    if event.key == pygame.K_SPACE:
                        self.en_pause = not self.en_pause
                        if not self.en_pause: self.compteur_stagnation = 0
                    elif event.key == pygame.K_c and self.en_pause:
                        self.reset_jeu()
                    elif event.key == pygame.K_r and self.en_pause:
                        self.recentrer_camera()

            # --- SOURIS (CLIC) ---
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clic Gauche
                    if self.en_menu:
                        for btn in self.boutons: # Délégation aux boutons
                            btn.check_click((mx, my))
                    else:
                        if self.en_pause:
                            # Mode Dessin
                            gx, gy = self.ecran_vers_grille(mx, my)
                            self.grille.ajouter_ou_supprimer(gx, gy)
                        else:
                            # Mode Drag (Caméra)
                            self.dragging = True
                # Zoom Molette
                elif event.button == 4: 
                    self.taille_cellule = min(100, self.taille_cellule + 2)
                elif event.button == 5: 
                    self.taille_cellule = max(4, self.taille_cellule - 2)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: self.dragging = False

            # --- SOURIS (MOUVEMENT) ---
            elif event.type == pygame.MOUSEMOTION:
                if self.en_menu:
                    for btn in self.boutons:
                        btn.check_hover((mx, my))
                elif self.dragging and not self.en_pause:
                    dx, dy = event.rel 
                    self.offset_x += dx
                    self.offset_y += dy

    # --- BOUCLE DE SIMULATION ---
    def update(self):
        if not self.en_pause and not self.en_menu:
            maintenant = pygame.time.get_ticks()
            # Timer pour contrôler la vitesse d'évolution
            if maintenant - self.dernier_update > self.vitesse_simulation:
                a_bouge = self.grille.evoluer()
                self.dernier_update = maintenant
                
                # Gestion Auto-Reset si stagnation
                if not a_bouge:
                    self.compteur_stagnation += 1
                    if self.compteur_stagnation >= self.SEUIL_STAGNATION:
                        self.reset_jeu()
                else:
                    self.compteur_stagnation = 0

    # --- MOTEUR DE RENDU ---
    def dessiner_grillage(self):
        """Optimisation : Ne dessine que les lignes visibles à l'écran"""
        start_col = -self.offset_x // self.taille_cellule
        end_col = start_col + (self.largeur_ecran // self.taille_cellule) + 2
        start_row = -self.offset_y // self.taille_cellule
        end_row = start_row + (self.hauteur_ecran // self.taille_cellule) + 2

        # Lignes verticales
        for c in range(int(start_col), int(end_col)):
            x = (c * self.taille_cellule) + self.offset_x
            pygame.draw.line(self.screen, GRIS_CLAIR, (x, 0), (x, self.hauteur_ecran))
        # Lignes horizontales
        for r in range(int(start_row), int(end_row)):
            y = (r * self.taille_cellule) + self.offset_y
            pygame.draw.line(self.screen, GRIS_CLAIR, (0, y), (self.largeur_ecran, y))

    def afficher_hud(self):
        """Affiche les infos en superposition (Overlay)"""
        # Info Génération
        info_gen = f"Génération: {self.grille.generation}"
        if self.compteur_stagnation > 0:
            info_gen += f" | Stagnation: {self.compteur_stagnation}/{self.SEUIL_STAGNATION}"
        
        txt_gen = self.font_ui.render(info_gen, True, NOIR)
        self.screen.blit(txt_gen, (self.largeur_ecran - txt_gen.get_width() - 10, 10))

        # Info Vitesse
        txt_speed = self.font_ui.render(f"Vitesse: {self.speed_level}/10", True, GRIS_FONCE)
        self.screen.blit(txt_speed, (self.largeur_ecran - txt_speed.get_width() - 10, 30))

        # Rappel Menu
        txt = self.font_ui.render("ECHAP : MENU & OPTIONS", True, GRIS_FONCE)
        self.screen.blit(txt, (10, 10))

    def afficher_menu(self):
        """Affiche la modale de menu (Fond transparent + Contrôles)"""
        # 1. Fond assombri
        s = pygame.Surface((self.largeur_ecran, self.hauteur_ecran))
        s.set_alpha(210) 
        s.fill(BLANC)
        self.screen.blit(s, (0,0))

        cx = self.largeur_ecran // 2
        cy = self.hauteur_ecran // 2

        # 2. Cadre Principal
        rect_menu = pygame.Rect(cx - 250, cy - 250, 500, 500)
        pygame.draw.rect(self.screen, BLEU_MENU, rect_menu, border_radius=15)
        pygame.draw.rect(self.screen, NOIR, rect_menu, 3, border_radius=15)

        # 3. Titre
        titre = self.font_titre.render("RÉGLAGES & COMMANDES", True, BLANC)
        self.screen.blit(titre, (cx - titre.get_width()//2, rect_menu.y + 20))

        # 4. Boutons interactifs
        for btn in self.boutons:
            btn.dessiner(self.screen, self.font_menu)

        # 5. Indicateurs Vitesse (Statique)
        txt_vit = self.font_menu.render(f"Vitesse: {self.speed_level}", True, BLANC)
        txt_ms = self.font_ui.render(f"({self.vitesse_simulation} ms)", True, GRIS_CLAIR)
        self.screen.blit(txt_vit, (cx - txt_vit.get_width()//2, cy + 160))
        self.screen.blit(txt_ms, (cx - txt_ms.get_width()//2, cy + 185))

        # 6. Liste des commandes (Statique)
        x_keys = cx + 10
        y_keys = cy - 80
        pygame.draw.line(self.screen, BLANC, (cx, cy - 90), (cx, cy + 130), 2) # Séparateur

        commandes = [
            ("SOURIS G", "Dessiner (Pause)"),
            ("SOURIS G", "Bouger (Lecture)"),
            ("MOLETTE", "Zoomer / Dézoomer"),
            ("ESPACE", "Lecture / Pause"),
            ("C", "Vider la grille"),
            ("R", "Recentrer Caméra"),
            ("F11", "Plein Écran"),
            ("ECHAP", "Menu / Retour")
        ]

        for i, (touche, desc) in enumerate(commandes):
            txt_t = self.font_info.render(f"[{touche}]", True, (255, 255, 100)) # Jaune
            txt_d = self.font_info.render(desc, True, BLANC)
            self.screen.blit(txt_t, (x_keys + 10, y_keys + i*28))
            self.screen.blit(txt_d, (x_keys + 100, y_keys + i*28))

    def afficher(self):
        """Pipeline de rendu principal"""
        self.screen.fill(BLANC)
        self.dessiner_grillage()

        # Dessin des cellules (avec Clipping pour perfs)
        for (gx, gy) in self.grille.cellules:
            px, py = self.grille_vers_ecran(gx, gy)
            # On saute le dessin si hors de l'écran
            if px < -self.taille_cellule or px > self.largeur_ecran or py < -self.taille_cellule or py > self.hauteur_ecran:
                continue
            rect = pygame.Rect(px + 1, py + 1, self.taille_cellule - 1, self.taille_cellule - 1)
            pygame.draw.rect(self.screen, NOIR, rect)

        self.afficher_hud()
        if self.en_menu: self.afficher_menu()

        pygame.display.flip() # Swap buffers

    def run(self):
        """Boucle principale (Game Loop)"""
        while True:
            self.gestion_evenements()
            self.update()
            self.afficher()
            self.clock.tick(FPS)

if __name__ == "__main__":
    jeu = Jeu()
    jeu.run()