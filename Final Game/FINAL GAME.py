import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Initialize Pygame Mixer
pygame.mixer.init()

# Screen settings
WIDTH, HEIGHT = 1920 , 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Background Music 
pygame.mixer.music.load("Background_music.wav")
pygame.mixer.music.play(-1)  # -1 makes it loop indefinitely

# Game Sound Effects
shoot_sound = pygame.mixer.Sound ("bullet_sound.wav") 
asteroid_hit_sound = pygame.mixer.Sound ("hit_sound.wav")
explosion_spaceship_sound = pygame.mixer.Sound ("Explosion_spaceship.wav")
powerup_spaceship_sound = pygame.mixer.Sound ("powerup_spaceship.wav")
gameover_sound = pygame.mixer.Sound ("game_over_sound.wav")
gameover_sound2 = pygame.mixer.Sound ("gameover_voice.wav")
gameover_sound3 = pygame.mixer.Sound ("gameover3_sound.wav")
option_sound = pygame.mixer.Sound ("click_option_sound.wav")

# Game Background Images
menu_background_image = pygame.image.load ("menu_background.jpg")
ingame_background_image = pygame.image.load ("ing2.jpg")
ingame_image = pygame.transform.scale(ingame_background_image, (WIDTH, HEIGHT))
background_image = pygame.transform.scale(menu_background_image, (WIDTH, HEIGHT))
asteroid_image = pygame.image.load ("asteroid.png")
asteroid_image = pygame.transform.scale (asteroid_image, (350, 350))
spaceship_image = pygame.image.load ("spaceship.png")
spaceship_image = pygame.transform.scale (spaceship_image, (150, 200))
bullet_image = pygame.image.load ("bullet.png")
bullet_image = pygame.transform.scale(bullet_image, (20, 50))
invicivility_image = pygame.image.load ("shield.png")
invicivility_image = pygame.transform.scale (invicivility_image, (50,50))
triple_points_image = pygame.image.load ("star.png")
triple_points_image = pygame.transform.scale (triple_points_image, (50,50))
triple_bullet_image = pygame.image.load ("triplebulet.png")
triple_bullet_image = pygame.transform.scale (triple_bullet_image, (50,50))

# Add vibration variables
VIBRATION_DURATION = 500  # Duration of vibration in milliseconds
VIBRATION_INTENSITY = 5   # Maximum pixel offset for vibration
vibration_start = 0
is_vibrating = False
original_ship_pos = None

def apply_vibration(rect, current_time):
    global is_vibrating, vibration_start, original_ship_pos
    
    if is_vibrating:
        elapsed = current_time - vibration_start
        if elapsed < VIBRATION_DURATION:
            # Calculate vibration offset using sine waves for more natural feel
            offset_x = math.sin(elapsed * 0.1) * VIBRATION_INTENSITY
            offset_y = math.cos(elapsed * 0.1) * VIBRATION_INTENSITY
            
            # Apply the offset but return to original position
            rect.x = original_ship_pos[0] + offset_x
            rect.y = original_ship_pos[1] + offset_y
        else:
            # Stop vibration and reset position
            is_vibrating = False
            rect.x, rect.y = original_ship_pos
            original_ship_pos = None

def start_vibration(rect, current_time):
    global is_vibrating, vibration_start, original_ship_pos
    is_vibrating = True
    vibration_start = current_time
    original_ship_pos = (rect.x, rect.y)

# Title Screen Function with Intensity Levels
def show_title_screen():
    title_font = pygame.font.Font("PublicPixel-rv0pA.ttf", 75)
    instruction_font = pygame.font.Font("PublicPixel-rv0pA.ttf", 36)
    levels = ["Easy", "Medium", "Hard", "Extreme"]
    selected_level = 0

    title_y_pos = + 350
    level_y_start = HEIGHT // 2  
    level_spacing = 75

    while True:
        screen.fill(BLACK)
        screen.blit(background_image, (0, 0))
        title_text = title_font.render("Asteroid Assault", True, PURPLE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, title_y_pos))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                # Allow both arrow keys and WASD for navigation
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected_level = (selected_level + 1) % len(levels)
                    option_sound.play()
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected_level = (selected_level - 1) % len(levels)
                    option_sound.play()
                elif event.key == pygame.K_RETURN:
                    option_sound.play()
                    return selected_level

        for i, level in enumerate(levels):
            color = BLUE if i == selected_level else WHITE 
            level_text = instruction_font.render(level, True, color)
            screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, level_y_start + i * level_spacing))

        pygame.display.flip()

# Show title screen before starting the game
selected_level = show_title_screen()

# Load spaceship
def draw_spaceship(color):
    spaceship_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.polygon(spaceship_img, color, [(25, 0), (50, 50), (25, 40), (0, 50)])
    return spaceship_image

# Game variables
spaceship_color = WHITE
spaceship_image = draw_spaceship(spaceship_color)
spaceship_rect = spaceship_image.get_rect(center=(WIDTH // 2, HEIGHT - 50))

bullets = []
asteroids = []
powerups = []
score = 0
lives = 3
game_over = False
font = pygame.font.Font(None, 28)

# Combo system variables
combo_count = 0
combo_timer = 0
COMBO_TIMEOUT = 2000
max_combo = 0
combo_multiplier = 1.0

# Power-up system
class PowerUp:
    def __init__(self, type_name, duration):
        self.type = type_name
        self.active = False
        self.start_time = 0
        self.duration = duration
        self.timer_text = ""

powerups_status = {
    "invincibility": PowerUp("invincibility", 7000),
    "triple_points": PowerUp("triple_points", 7000),
    "power_boost": PowerUp("power_boost", 7000)
}

# Difficulty settings based on selected level
def apply_difficulty_settings(level):
    settings = {
        0: {"asteroid_spawn_rate": 60, "asteroid_speed": (2, 5), "powerup_spawn_rate": 200},
        1: {"asteroid_spawn_rate": 45, "asteroid_speed": (3, 6), "powerup_spawn_rate": 250},
        2: {"asteroid_spawn_rate": 30, "asteroid_speed": (4, 7), "powerup_spawn_rate": 300},
        3: {"asteroid_spawn_rate": 15, "asteroid_speed": (5, 8), "powerup_spawn_rate": 350}
    }
    return settings[level]

difficulty = apply_difficulty_settings(selected_level)

def create_asteroid():
    x = random.randint(0, WIDTH)
    y = random.randint(-100, -40)
    min_speed, max_speed = difficulty["asteroid_speed"]
    speed = random.uniform(min_speed, max_speed)
    asteroid_rect = pygame.Rect(x, y, 180, 10)  # Use consistent size
    return {"rect": asteroid_rect, "speed": speed, "image": asteroid_image}

def create_bullet(x, y):
    bullet_rect = pygame.Rect(x, y, bullet_image.get_width(), bullet_image.get_height())
    return {"rect": bullet_rect, "image": bullet_image}

def create_powerup():
    x = random.randint(0, WIDTH - 30)
    y = random.randint(-100, -40)
    powerup_type = random.choice(["invincibility", "power_boost", "triple_points"])

    if powerup_type == "invincibility":
        image = invicivility_image
    elif powerup_type == "power_boost":
        image = triple_bullet_image
    elif powerup_type == "triple_points":
        image = triple_points_image
    return {"rect": pygame.Rect(x, y, 30, 30), "type": powerup_type, "image": image}

def activate_powerup(powerup_type):
    current_time = pygame.time.get_ticks()
    power = powerups_status[powerup_type]
    power.active = True
    power.start_time = current_time
    return f"{powerup_type.replace('_', ' ').title()} Activated!"

def update_powerups(current_time):
    global spaceship_color
    active_effects = []
    
    for power in powerups_status.values():
        if power.active:
            remaining_time = (power.duration - (current_time - power.start_time)) // 1000
            if remaining_time <= 0:
                power.active = False
                spaceship_color = WHITE
            else:
                # Update the timer text based on the power-up type
                if power.type == "invincibility":
                    power.timer_text = f"Invincibility Shield: {remaining_time}s"
                    screen.blit(invicivility_image, spaceship_rect.topleft)
                elif power.type == "power_boost":
                    power.timer_text = f"Laser Boosters: {remaining_time}s"
                    screen.blit(triple_bullet_image, spaceship_rect.topright)
                elif power.type == "triple_points":
                    power.timer_text = f"3x Score Multiplier: {remaining_time}s"
                    screen.blit(triple_points_image, spaceship_rect.bottomleft)
                
                active_effects.append(power.type)
    
    return active_effects

def reset_combo():
    global combo_count, combo_multiplier
    combo_count = 0
    combo_multiplier = 1.0

def restart_game():
    global bullets, asteroids, powerups, score, lives, game_over, combo_count, max_combo, spaceship_color
    global combo_multiplier
    bullets.clear()
    asteroids.clear()
    powerups.clear()
    score = 0
    lives = 3
    combo_count = 0
    max_combo = 0
    combo_multiplier = 1.0
    game_over = False
    spaceship_color = WHITE
    for power in powerups_status.values():
        power.active = False

# Game loop
clock = pygame.time.Clock()
running = True
start_time = pygame.time.get_ticks()

while running:
    current_time = pygame.time.get_ticks()
    screen.fill(BLACK)
    screen.blit(ingame_image, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                shoot_sound.play()
                if powerups_status["power_boost"].active:
                    bullets.extend([
                        pygame.Rect(spaceship_rect.centerx - 15, spaceship_rect.centery, 5, 10),
                        pygame.Rect(spaceship_rect.centerx, spaceship_rect.centery, 5, 10),
                        pygame.Rect(spaceship_rect.centerx + 15, spaceship_rect.centery, 5, 10)
                    ])
                else:
                    bullets.append(pygame.Rect(spaceship_rect.centerx, spaceship_rect.centery, 5, 10))
            if event.key == pygame.K_r and game_over:
                restart_game()
                option_sound.play()
                gameover_sound3.stop()
                pygame.mixer.music.load("Background_music.wav")
                pygame.mixer.music.play(-1)
                start_time = pygame.time.get_ticks()
            if event.key == pygame.K_m and game_over:
                option_sound.play()
                gameover_sound3.stop()
                pygame.mixer.music.load("Background_music.wav")
                pygame.mixer.music.play(-1)
                selected_level = show_title_screen()
                difficulty = apply_difficulty_settings(selected_level)
                restart_game()

    if not game_over:
        
        # Apply vibration effect
        apply_vibration(spaceship_rect, current_time)
        # Update combo timer
        if combo_count > 0 and current_time > combo_timer + COMBO_TIMEOUT:
            reset_combo()
        # Update powerups
        active_effects = update_powerups(current_time)

        # Spaceship movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and spaceship_rect.left > 0:
            spaceship_rect.x -= 7
        if keys[pygame.K_RIGHT] and spaceship_rect.right < WIDTH:
            spaceship_rect.x += 7
        if keys[pygame.K_UP] and spaceship_rect.top > 0:
            spaceship_rect.y -= 5
        if keys[pygame.K_DOWN] and spaceship_rect.bottom < HEIGHT:
            spaceship_rect.y += 5

        # WASD keys for movement
        if keys[pygame.K_a] and spaceship_rect.left > 0:
             spaceship_rect.x -= 7
        if keys[pygame.K_d] and spaceship_rect.right < WIDTH:
            spaceship_rect.x += 7
        if keys[pygame.K_w] and spaceship_rect.top > 0:
            spaceship_rect.y -= 5
        if keys[pygame.K_s] and spaceship_rect.bottom < HEIGHT:
            spaceship_rect.y += 5 

        # Update bullets
        for bullet in bullets[:]:
            bullet.y -= 15
            if bullet.y < 0:
                bullets.remove(bullet)

        # Spawn game objects
        if random.randint(0, difficulty["asteroid_spawn_rate"]) == 0:
            asteroids.append(create_asteroid())
        if random.randint(0, difficulty["powerup_spawn_rate"]) == 0:
            powerups.append(create_powerup())

        # Collision checks
        for asteroid in asteroids[:]:
            screen.blit(asteroid["image"], (asteroid["rect"].x, asteroid["rect"].y))
            asteroid["rect"].y += asteroid["speed"]
            if asteroid["rect"].top > HEIGHT:
                asteroids.remove(asteroid) 
                reset_combo()
                continue
            if spaceship_rect.colliderect(asteroid["rect"]):
                if not powerups_status["invincibility"].active:
                    explosion_spaceship_sound.play()
                    lives -= 1
                    reset_combo()
                    # Start vibration effect when hit
                    start_vibration(spaceship_rect, current_time)
                    if lives == 0:
                        pygame.mixer.music.stop()
                        gameover_sound.play()
                        gameover_sound2.play()
                        gameover_sound3.play()
                        game_over = True
                asteroids.remove(asteroid)
                break

        for powerup in powerups[:]:
            powerup["rect"].y += 5
            if powerup["rect"].top > HEIGHT:
                powerups.remove(powerup)
            if spaceship_rect.colliderect(powerup["rect"]):
                powerup_spaceship_sound.play()
                activate_powerup(powerup["type"])
                powerups.remove(powerup)

        for bullet in bullets[:]:
            bullet_hit = False
            for asteroid in asteroids[:]:
                # Print positions for debugging
                if bullet.colliderect(asteroid["rect"]):
                    asteroid_hit_sound.play()
                    # Update score based on combo system and power-ups
                    base_points = 10
                    if powerups_status["triple_points"].active:
                        base_points *= 3
                    
                    # Update combo system
                    combo_count += 1
                    if combo_count > max_combo:
                        max_combo = combo_count
                    
                    # Calculate combo multiplier (increases by 0.1 for each hit, max 3.0)
                    combo_multiplier = min(1.0 + (combo_count * 0.1), 3.0)
                    
                    # Apply combo multiplier to score
                    score += base_points * combo_multiplier
                    
                    # Reset combo timer
                    combo_timer = current_time
                    
                    # Remove both bullet and asteroid
                    bullets.remove(bullet)
                    asteroids.remove(asteroid)
                    bullet_hit = True
                    break
            if bullet_hit:
                    break

        # Drawing
        spaceship_image = draw_spaceship(spaceship_color)
        screen.blit(spaceship_image, spaceship_rect)

        for bullet in bullets:
            screen.blit(bullet_image, bullet)

        for asteroid in asteroids:
            screen.blit(asteroid["image"], asteroid["rect"])

        for powerup in powerups: 
            screen.blit(powerup["image"], powerup["rect"].topleft)

        # UI Elements
        # Score and lives (left side)
        score_text = font.render(f'SCORE: {int(score)}', True, WHITE)
        lives_text = font.render(f'Lives: ', True, WHITE)
        screen.blit(score_text, (10, 10))
        for i in range(lives):
            pygame.draw.rect(screen, RED, (10 + i * 20, 30, 15, 15))

        # Timer
        elapsed_time = (current_time - start_time) // 1000
        timer_text = font.render(f'TIMER: {elapsed_time}', True, WHITE)
        screen.blit(timer_text, (10, 50))

        # Combo system (right side
        combo_text = font.render(f'COMBO: {combo_count} (x{combo_multiplier:.1f})', True, WHITE)
        max_combo_text = font.render(f'MAX COMBO: {max_combo}', True, WHITE)
        screen.blit(combo_text, (WIDTH - 200, 10))
        screen.blit(max_combo_text, (WIDTH - 200, 40))

        if combo_count > 0:
            combo_duration = COMBO_TIMEOUT - (current_time - combo_timer)
            combo_percentage = max(0, combo_duration / COMBO_TIMEOUT)
            pygame.draw.rect(screen, GREEN, (WIDTH - 200, 70, 150 * combo_percentage, 10))

        # Power-up timers (center-right)
        y_offset = 100
        for power in powerups_status.values():
            if power.active:
                timer_text = font.render(power.timer_text, True, WHITE)
                screen.blit(timer_text, (WIDTH - 200, y_offset))
                y_offset += 30

    else:
        restart1_font = pygame.font.Font("PublicPixel-rv0pA.ttf", 75)
        restart2_font = pygame.font.Font("PublicPixel-rv0pA.ttf", 40)
        game_over_text = restart1_font.render("GAME OVER", True, RED)
        restart_text = restart2_font.render("Press R to Restart or M for Menu", True, BLUE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
