
def test_pyglet_pygame():

    #import pygame
    import pyglet_pygame as pygame
    from random import randint, choice

    def draw_speed_test(surfs, d):
        d.fill((0,0,0))
        for i in range(50):
            rand_surf = choice(surfs)
            rand_pos = randint(0, d.get_width()), randint(0, d.get_height())

            d.blit(rand_surf, rand_pos)
        pygame.display.update()

    def draw_and_save_comparison(surfs, d):
        d.fill((0,0,0))
        d.blit(surfs[0], (0, 0))
        d.blit(surfs[1], (256, 0))
        d.blit(surfs[2], (256+128, 0))
        d.blit(surfs[3], (256+128+64, 0))
        d.blit(surfs[4], (0, 256))
        d.blit(surfs[5], (512, 256))
        pygame.display.update()
        pygame.image.save(d, "screenshot.png")

    pygame.init()
    d = pygame.display.set_mode((1600, 800), pygame.HWSURFACE)

    image_surf = pygame.image.load("pyglet_pygame/test_image.png")

    rect = pygame.Rect(0, 0, 128, 128)

    sub_surf = image_surf.subsurface(rect)

    rect_2 = pygame.Rect(0, 0, 64, 64)
    sub_surf_2 = sub_surf.subsurface(rect_2)

    scaled_surf = pygame.transform.scale(sub_surf, (256, 256))

    flipped_surf = pygame.transform.flip(image_surf, 1, 0)

    rot_surf = pygame.transform.rotate(scaled_surf, 45) 

    other_surf = pygame.Surface((256, 256))
    other_surf.blit(sub_surf, (0, 0))

    surfs = image_surf, sub_surf, sub_surf_2, scaled_surf, rot_surf, flipped_surf

    clock = pygame.time.Clock()
    fps = 144

    while True:
        

        #draw_speed_test(surfs, d)
        draw_and_save_comparison(surfs, d)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
        
        clock.tick(fps)
        pygame.display.set_caption(str(clock.get_fps()))

def test_json():
    import json
    with open("door_closed.json", "r") as f:
        d = json.load(f)

    
test_json()