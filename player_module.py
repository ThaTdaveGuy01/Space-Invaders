import pygame
import os
import random

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600  # Keep screen dimensions consistent

def remove_color(image, color):
    """Removes a specific color and makes it transparent."""
    image.set_colorkey(color)
    return image

def change_color(image, old_color, new_color):
    """
    Replaces all pixels of a given color in an image with a new color.
    :param image: The Pygame surface to modify.
    :param old_color: The color to replace (tuple, RGB).
    :param new_color: The replacement color (tuple, RGB).
    :return: The modified Pygame surface.
    """
    image = image.copy()  # Create a copy to avoid modifying the original
    width, height = image.get_size()
    for x in range(width):
        for y in range(height):
            if image.get_at((x, y))[:3] == old_color:  # Check for color match (ignore alpha)
                image.set_at((x, y), new_color + (image.get_at((x, y))[3],))  # Replace color
    return image

class Player(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, index=1, left_key=pygame.K_a, right_key=pygame.K_d):
        """
        Initializes the Player object.
        :param screen_width: Width of the game screen.
        :param screen_height: Height of the game screen.
        :param index: Index of the player (e.g., Player 1, Player 2).
        :param left_key: Key for moving left.
        :param right_key: Key for moving right.
        """
        super().__init__()
        self.index = index
        self.left_key = left_key
        self.right_key = right_key
        self.lives = 3  # Each player starts with 3 lives

        # Load the player image
        player_path = os.path.join("Textures", "Player.png")
        self.image = pygame.image.load(player_path).convert()
        self.image = remove_color(self.image, (255, 0, 255))  # Remove magenta filler

        # Default color change (white -> player's unique color)
        if self.index == 1:
            self.image = change_color(self.image, (255, 255, 255), (255, 0, 0))  # Red for Player 1
        else:
            self.image = change_color(self.image, (255, 255, 255), (0, 0, 255))  # Blue for Player 2

        # Set up the player's rectangle
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height - 50)
        self.speed = 5

    def update(self, keys):
        """Updates the player's position based on key inputs."""
        if keys[self.left_key]:
            self.rect.x -= self.speed
        if keys[self.right_key]:
            self.rect.x += self.speed

        # Keep the player on the screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def set_color(self, new_color):
        """
        Changes the player's color by replacing white pixels with a new color.
        :param new_color: The new color to apply (tuple, RGB).
        """
        self.image = change_color(self.image, (255, 255, 255), new_color)

    def set_controls(self, left_key, right_key):
        """
        Updates the player's controls.
        :param left_key: New key for moving left.
        :param right_key: New key for moving right.
        """
        self.left_key = left_key
        self.right_key = right_key

    def take_damage(self, amount):
        """
        Reduces the player's lives by the specified amount.
        :param amount: The amount of damage to take.
        """
        self.lives = max(0, self.lives - amount)  # Ensure lives don't go below 0
    def heal(self):
        self.lives = max(0, self.lives == 3)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_enemy=False):
        """
        Initializes the Bullet object with animation and explosion effects.
        :param x: Initial x-coordinate of the bullet.
        :param y: Initial y-coordinate of the bullet.
        :param is_enemy: Boolean indicating if the bullet belongs to an enemy.
        """
        super().__init__()
        self.is_enemy = is_enemy
        self.images = [
            remove_color(pygame.image.load(os.path.join("Textures", "EnemyBullet1.png" if is_enemy else "PlayerBullet1.png")).convert(), (255, 0, 255)),
            remove_color(pygame.image.load(os.path.join("Textures", "EnemyBullet2.png" if is_enemy else "PlayerBullet2.png")).convert(), (255, 0, 255))
        ]
        self.explosion_images = [
            remove_color(pygame.image.load(os.path.join("Textures", "ExplosionPhase1.png")).convert(), (255, 0, 255)),
            remove_color(pygame.image.load(os.path.join("Textures", "ExplosionPhase2.png")).convert(), (255, 0, 255)),
            remove_color(pygame.image.load(os.path.join("Textures", "ExplosionPhase3.png")).convert(), (255, 0, 255))
        ]
        self.image_index = 0
        self.image = self.images[self.image_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 5 if is_enemy else -5  # Enemy bullets go down, player bullets go up
        self.exploding = False
        self.explosion_index = 0
        self.explosion_timer = 0

    def update(self):
        """Updates the bullet's position or handles the explosion animation."""
        if self.exploding:
            self.explosion_timer += 1
            if self.explosion_timer % 5 == 0:  # Change explosion frame every 5 ticks
                self.explosion_index += 1
                if self.explosion_index < len(self.explosion_images):
                    self.image = self.explosion_images[self.explosion_index]
                else:
                    self.kill()  # Remove the bullet when the explosion ends
        else:
            self.rect.y += self.speed
            self.image_index = (self.image_index + 1) % len(self.images)  # Cycle through bullet frames
            self.image = self.images[self.image_index]
            if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
                self.trigger_explosion()  # Trigger explosion near the wall

    def trigger_explosion(self):
        """Triggers the explosion animation."""
        self.exploding = True
        self.image = self.explosion_images[0]
        self.rect = self.image.get_rect(center=self.rect.center)

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        """
        Initializes the Wall object.
        :param x: Initial x-coordinate of the wall.
        :param y: Initial y-coordinate of the wall.
        """
        super().__init__()
        self.states = [
            os.path.join("Textures", "WallState1.png"),
            os.path.join("Textures", "WallState2.png"),
            os.path.join("Textures", "WallState3.png")
        ]
        self.image = pygame.image.load(self.states[0]).convert()
        self.image = remove_color(self.image, (255, 0, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 15
        self.state_index = 0

    def take_damage(self):
        """Reduces the wall's health and updates its state."""
        self.health -= 1
        if self.health <= 6 and self.state_index < 2:  # Transition to next state
            self.state_index += 1
            self.image = pygame.image.load(self.states[self.state_index]).convert()
            self.image = remove_color(self.image, (255, 0, 255))
        if self.health <= 0:  # Wall is destroyed
            self.kill()

    def reset(self):
        """Resets the wall to its initial state."""
        self.health = 15
        self.state_index = 0
        self.image = pygame.image.load(self.states[self.state_index]).convert()
        self.image = remove_color(self.image, (255, 0, 255))

import pygame
import os
import random

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600  # Keep screen dimensions consistent

def remove_color(image, color):
    """Removes a specific color and makes it transparent."""
    image.set_colorkey(color)
    return image

def change_color(image, old_color, new_color):
    """
    Replaces all pixels of a given color in an image with a new color.
    :param image: The Pygame surface to modify.
    :param old_color: The color to replace (tuple, RGB).
    :param new_color: The replacement color (tuple, RGB).
    :return: The modified Pygame surface.
    """
    image = image.copy()  # Create a copy to avoid modifying the original
    width, height = image.get_size()
    for x in range(width):
        for y in range(height):
            if image.get_at((x, y))[:3] == old_color:  # Check for color match (ignore alpha)
                image.set_at((x, y), new_color + (image.get_at((x, y))[3],))  # Replace color
    return image

class Player(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, index=1, left_key=pygame.K_a, right_key=pygame.K_d):
        """
        Initializes the Player object.
        :param screen_width: Width of the game screen.
        :param screen_height: Height of the game screen.
        :param index: Index of the player (e.g., Player 1, Player 2).
        :param left_key: Key for moving left.
        :param right_key: Key for moving right.
        """
        super().__init__()
        self.index = index
        self.left_key = left_key
        self.right_key = right_key
        self.lives = 3  # Each player starts with 3 lives

        # Load the player image
        player_path = os.path.join("Textures", "Player.png")
        self.image = pygame.image.load(player_path).convert()
        self.image = remove_color(self.image, (255, 0, 255))  # Remove magenta filler

        # Default color change (white -> player's unique color)
        if self.index == 1:
            self.image = change_color(self.image, (255, 255, 255), (255, 0, 0))  # Red for Player 1
        else:
            self.image = change_color(self.image, (255, 255, 255), (0, 0, 255))  # Blue for Player 2

        # Set up the player's rectangle
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height - 50)
        self.speed = 5

    def update(self, keys):
        """Updates the player's position based on key inputs."""
        if keys[self.left_key]:
            self.rect.x -= self.speed
        if keys[self.right_key]:
            self.rect.x += self.speed

        # Keep the player on the screen
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def set_color(self, new_color):
        """
        Changes the player's color by replacing white pixels with a new color.
        :param new_color: The new color to apply (tuple, RGB).
        """
        self.image = change_color(self.image, (255, 255, 255), new_color)

    def set_controls(self, left_key, right_key):
        """
        Updates the player's controls.
        :param left_key: New key for moving left.
        :param right_key: New key for moving right.
        """
        self.left_key = left_key
        self.right_key = right_key

    def take_damage(self, amount):
        """
        Reduces the player's lives by the specified amount.
        :param amount: The amount of damage to take.
        """
        self.lives = max(0, self.lives - amount)  # Ensure lives don't go below 0

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_enemy=False):
        """
        Initializes the Bullet object with animation and explosion effects.
        :param x: Initial x-coordinate of the bullet.
        :param y: Initial y-coordinate of the bullet.
        :param is_enemy: Boolean indicating if the bullet belongs to an enemy.
        """
        super().__init__()
        self.is_enemy = is_enemy
        self.images = [
            remove_color(pygame.image.load(os.path.join("Textures", "EnemyBullet1.png" if is_enemy else "PlayerBullet1.png")).convert(), (255, 0, 255)),
            remove_color(pygame.image.load(os.path.join("Textures", "EnemyBullet2.png" if is_enemy else "PlayerBullet2.png")).convert(), (255, 0, 255))
        ]
        self.explosion_images = [
            remove_color(pygame.image.load(os.path.join("Textures", "ExplosionPhase1.png")).convert(), (255, 0, 255)),
            remove_color(pygame.image.load(os.path.join("Textures", "ExplosionPhase2.png")).convert(), (255, 0, 255)),
            remove_color(pygame.image.load(os.path.join("Textures", "ExplosionPhase3.png")).convert(), (255, 0, 255))
        ]
        self.image_index = 0
        self.image = self.images[self.image_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 5 if is_enemy else -5  # Enemy bullets go down, player bullets go up
        self.exploding = False
        self.explosion_index = 0
        self.explosion_timer = 0

    def update(self):
        """Updates the bullet's position or handles the explosion animation."""
        if self.exploding:
            self.explosion_timer += 1
            if self.explosion_timer % 5 == 0:  # Change explosion frame every 5 ticks
                self.explosion_index += 1
                if self.explosion_index < len(self.explosion_images):
                    self.image = self.explosion_images[self.explosion_index]
                else:
                    self.kill()  # Remove the bullet when the explosion ends
        else:
            self.rect.y += self.speed
            self.image_index = (self.image_index + 1) % len(self.images)  # Cycle through bullet frames
            self.image = self.images[self.image_index]
            if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
                self.trigger_explosion()  # Trigger explosion near the wall

    def trigger_explosion(self):
        """Triggers the explosion animation."""
        self.exploding = True
        self.image = self.explosion_images[0]
        self.rect = self.image.get_rect(center=self.rect.center)

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        """
        Initializes the Wall object.
        :param x: Initial x-coordinate of the wall.
        :param y: Initial y-coordinate of the wall.
        """
        super().__init__()
        self.states = [
            os.path.join("Textures", "WallState1.png"),
            os.path.join("Textures", "WallState2.png"),
            os.path.join("Textures", "WallState3.png")
        ]
        self.image = pygame.image.load(self.states[0]).convert()
        self.image = remove_color(self.image, (255, 0, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 25
        self.state_index = 0

    def take_damage(self):
        """Reduces the wall's health and updates its state."""
        self.health -= 1
        if self.health <= 6 and self.state_index < 2:  # Transition to next state
            self.state_index += 1
            self.image = pygame.image.load(self.states[self.state_index]).convert()
            self.image = remove_color(self.image, (255, 0, 255))
        if self.health <= 0:  # Wall is destroyed
            self.kill()

    def reset(self):
        """Resets the wall to its initial state."""
        self.health = 10
        self.state_index = 0
        self.image = pygame.image.load(self.states[self.state_index]).convert()
        self.image = remove_color(self.image, (255, 0, 255))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path):
        """
        Initializes the Enemy object.
        :param x: Initial x-coordinate of the enemy.
        :param y: Initial y-coordinate of the enemy.
        :param image_path: Path to the enemy's image.
        """
        super().__init__()
        try:
            self.image = pygame.image.load(os.path.join("Textures", image_path)).convert()
        except FileNotFoundError:
            print(f"Error: Enemy texture '{image_path}' not found. Using default texture.")
            self.image = pygame.Surface((50, 40))  # Default size for enemies
            self.image.fill((255, 0, 0))  # Red placeholder for missing textures
        self.image.set_colorkey((255, 0, 255))  # Make pink color transparent
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 1
        self.speed = 10  # Keep speed as a whole number
        self.direction = 1  # 1 means moving right, -1 means moving left
        self.can_shoot = True
        self.shooting_timer = 10
        self.shooting_cooldown = 1  # Slows down enemy shooting
        self.move_delay = 10  # Number of frames to wait before moving
        self.current_frame = 0  # Frame counter for movement

    def update(self):
        # Move logic (same as before)
        self.current_frame += 1
        if self.current_frame >= self.move_delay:
            self.rect.x += self.speed * self.direction
            if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0:
                self.direction *= -1
                self.rect.y += 20
            self.current_frame = 0

    # Handle shooting cooldown
        if self.shooting_timer > 0:
            self.shooting_timer -= 1  # Decrease the timer
        else:
            self.can_shoot = True  # Allow shooting when cooldown is done

    def shoot(self):
        if self.can_shoot:
            self.can_shoot = False
            self.shooting_timer = self.shooting_cooldown  # Set cooldown
            return Bullet(self.rect.centerx, self.rect.bottom, is_enemy=True)
        return None

    def take_damage(self):
        """Reduces the enemy's health and removes it if health reaches zero."""
        self.health -= 1
        if self.health <= 0:
            self.kill()

    def set_color(self, color):
        """
        Changes the enemy's color by replacing all non-transparent pixels with the specified color.
        :param color: The new color to apply (tuple, RGB).
        """
        for x in range(self.image.get_width()):
            for y in range(self.image.get_height()):
                if self.image.get_at((x, y))[:3] != (255, 0, 255):  # Ignore transparent areas
                    self.image.set_at((x, y), color + (255,))