#!/usr/bin/env python3
"""
Batch image generation for Fooocus-API (mrhan1993/Fooocus-API).

SETUP:
1. Install Fooocus-API: https://github.com/mrhan1993/Fooocus-API
2. Run it: python main.py --port 8888
3. Run this script: python fooocus_batch_generate.py

All 69 frames will be generated and saved to ./output_frames/
"""

import requests
import json
import time
import os
import sys

# ============ CONFIG ============
FOOOCUS_HOST = "http://127.0.0.1:8888"
TEXT2IMG_ENDPOINT = "/v1/generation/text-to-image"
QUERY_JOB_ENDPOINT = "/v1/generation/query-job"
OUTPUT_DIR = "./output_frames"

# Generation settings
PERFORMANCE = "Speed"  # Speed, Quality, Extreme Speed
ASPECT_RATIO = "1152*896"  # wide for video frames (16:9-ish)
NEGATIVE_PROMPT = "realistic, photo, 3D render, gradient shading, complex shadows, blurry, watermark, text"
STYLE = "Fooocus V2"  # or "sai-anime", etc.
GUIDANCE_SCALE = 7.0
SHARPNESS = 2.0
STEPS = 30  # reduce for speed (20 for fast, 30 for quality)


# ============ ALL 69 PROMPTS ============
PROMPTS = [
    ("frame_01", "Minimalist 2D vector-art webcomic-style illustration of a destroyed Nazi flag on the ground, with a dark, ominous storm cloud looming in the background. Thick black outlines, flat colors, simplified shapes. Camera Angle: Wide shot. Lighting: Flat, minimal shading. Mood: Gloomy, foreboding. Action: Static symbolic scene."),
    ("frame_02", "Minimalist 2D vector-art webcomic-style illustration of an American soldier and a Soviet soldier standing back-to-back, side-eying each other with cynical, suspicious expressions. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Tense, suspicious. Action: Two former allies looking at each other with distrust."),
    ("frame_03", "Minimalist 2D vector-art webcomic-style illustration of a giant red button with a nuclear symbol, and two cartoonish hands hovering over it from opposite sides. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Tense, apocalyptic. Action: Hands hesitating over a launch button."),
    ("frame_04", "Minimalist 2D vector-art webcomic-style illustration of a cartoon Earth with a giant jagged crack splitting it in half, one side blue and the other side red. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Dramatic, educational. Action: The Earth splitting into two distinct halves."),
    ("frame_05", "Minimalist 2D vector-art webcomic-style illustration of the cynical host character (a young man with messy hair and bored eyes) pointing at a blackboard with a drawing of a bomb. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Cynical, humorous. Action: The host presenting a topic to the audience."),
    ("frame_06", "Minimalist 2D vector-art webcomic-style illustration of the cynical host holding an oversized smartphone displaying various social media logos. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Humorous, self-aware. Action: Host pointing at the smartphone screen."),
    ("frame_07", "Minimalist 2D vector-art webcomic-style illustration of a blue VKontakte logo next to a crude, funny cartoon stick-figure drawing representing a meme. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Humorous, informal. Action: Static display of graphic elements."),
    ("frame_08", "Minimalist 2D vector-art webcomic-style illustration of an orange Boosty logo with a glowing padlock icon over a film strip. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Exclusive, engaging. Action: Static display of graphic elements."),
    ("frame_09", "Minimalist 2D vector-art webcomic-style illustration of a blue Telegram paper plane flying out of a torn document page full of text. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Informative."),
    ("frame_10", "Minimalist 2D vector-art webcomic-style illustration of a purple Discord logo wearing a pair of headphones, with an arrow pointing downwards. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Welcoming. Action: Arrow pointing down to the description box."),

    ("frame_11", "Minimalist 2D vector-art webcomic-style illustration of the cynical host character crossing his arms and smirking slightly. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Cynical, confident. Action: Host striking a pose."),
    ("frame_12", "Minimalist 2D vector-art webcomic-style illustration of simplified, crumbled grey buildings and piles of rubble under a dark grey sky. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, minimal shading. Mood: Gloomy, desolate. Action: Static landscape of destruction."),
    ("frame_13", "Minimalist 2D vector-art webcomic-style illustration of anthropomorphized flags of Britain and France looking exhausted, sweating, and leaning on crutches. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Exhausted, pathetic. Action: Characters looking extremely tired."),
    ("frame_14", "Minimalist 2D vector-art webcomic-style illustration of two giant, muscular silhouettes stepping over the rubble of smaller nations. Thick black outlines, flat colors. Camera Angle: Low angle. Lighting: Flat, even lighting. Mood: Imposing, powerful. Action: Giants stepping forward."),
    ("frame_15", "Minimalist 2D vector-art webcomic-style illustration of a muscular American Uncle Sam and a muscular Soviet bear flexing their biceps at each other. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Aggressive, competitive. Action: Two figures flexing muscles."),
    ("frame_16", "Minimalist 2D vector-art webcomic-style illustration of a deep black chasm separating a dollar sign on the left and a hammer and sickle on the right. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Tense, divided. Action: Static infographic of a chasm."),
    ("frame_17", "Minimalist 2D vector-art webcomic-style illustration of a bustling cartoon city with a ballot box and money bags. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, bright lighting. Mood: Energetic, prosperous. Action: Coins falling into a bag next to a ballot box."),
    ("frame_18", "Minimalist 2D vector-art webcomic-style illustration of uniform factory buildings, a large gear, and a single red ballot box. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, industrial lighting. Mood: Rigid, ordered. Action: Gears turning on a factory."),
    ("frame_19", "Minimalist 2D vector-art webcomic-style illustration of an American and a Soviet character reluctantly shaking hands while both stomping on a caricature of Hitler. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Reluctant teamwork. Action: Handshake over a defeated enemy."),
    ("frame_20", "Minimalist 2D vector-art webcomic-style illustration of the American and Soviet characters immediately letting go of the handshake and pulling out boxing gloves. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Hostile. Action: Putting on boxing gloves."),

    ("frame_21", "Minimalist 2D vector-art webcomic-style illustration of Stalin, Roosevelt, and Churchill sitting at a round table, glaring at each other with cynical, annoyed expressions. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Tense, passive-aggressive. Action: Leaders glaring across a table."),
    ("frame_22", "Minimalist 2D vector-art webcomic-style illustration of three cartoon hands tearing apart a paper map of Europe. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Aggressive, greedy. Action: Hands ripping a map."),
    ("frame_23", "Minimalist 2D vector-art webcomic-style illustration of a sad, battered Soviet soldier looking at an endless field of simple cartoon wooden crosses. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, gloomy lighting. Mood: Somber, tragic. Action: Soldier looking at graves."),
    ("frame_24", "Minimalist 2D vector-art webcomic-style illustration of a giant red brick wall being built across a map of Eastern Europe. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Defensive, isolated. Action: Bricks being stacked into a wall."),
    ("frame_25", "Minimalist 2D vector-art webcomic-style illustration of a cartoon bear wearing a hard hat, placing a Keep Out sign next to a shield on a border. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Defensive. Action: Bear placing a warning sign."),
    ("frame_26", "Minimalist 2D vector-art webcomic-style illustration of a terrified American diplomat looking through binoculars at a red wave swallowing smaller countries. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Panicked, paranoid. Action: Looking through binoculars in fear."),
    ("frame_27", "Minimalist 2D vector-art webcomic-style illustration of an exaggerated cartoon Winston Churchill smoking a cigar at a podium with microphones. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Serious, historic. Action: Character giving a speech at a podium."),
    ("frame_28", "Minimalist 2D vector-art webcomic-style illustration of a massive, heavy iron curtain slamming down violently on a map of Europe, dividing it. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, dramatic lighting. Mood: Heavy, dividing. Action: Iron curtain falling down."),
    ("frame_29", "Minimalist 2D vector-art webcomic-style illustration of a starting pistol firing, but instead of a bullet, a snowflake comes out. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Cynical, symbolic. Action: Starting pistol firing a snowflake."),
    ("frame_30", "Minimalist 2D vector-art webcomic-style illustration of a stressed, sweating cartoon student looking at an exam paper with the words Cold War and question marks. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Stressed, relatable. Action: Student staring at an exam in panic."),

    ("frame_31", "Minimalist 2D vector-art webcomic-style illustration of a smiling female character with a pointer, pointing at a whiteboard that says History Exam 2025. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, bright lighting. Mood: Educational, helpful. Action: Character teaching at a whiteboard."),
    ("frame_32", "Minimalist 2D vector-art webcomic-style illustration of the cynical host character giving a thumbs up while holding a book titled History. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Recommending, positive. Action: Host give a thumbs up."),
    ("frame_33", "Minimalist 2D vector-art webcomic-style illustration of a YouTube player window showing the female teacher character explaining a timeline. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Educational. Action: A video playing inside a screen frame."),
    ("frame_34", "Minimalist 2D vector-art webcomic-style illustration of a pile of books and papers glowing with a golden aura, with an A+ grade hovering above. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Rewarding, helpful. Action: Static display of study materials."),
    ("frame_35", "Minimalist 2D vector-art webcomic-style illustration of a cartoon brain lifting weights shaped like historical artifacts. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Fun, active. Action: Brain exercising."),
    ("frame_36", "Minimalist 2D vector-art webcomic-style illustration of a large red cursor clicking on a Subscribe button under a video player. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Direct action. Action: Cursor clicking a button."),
    ("frame_37", "Minimalist 2D vector-art webcomic-style illustration of red paint spilling rapidly across a map, and a cartoon hand trying to stop it. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Urgent, alarming. Action: Paint spreading over a map."),
    ("frame_38", "Minimalist 2D vector-art webcomic-style illustration of an exaggerated cartoon Harry Truman putting up a sturdy wooden fence. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Determined. Action: Character building a fence."),
    ("frame_39", "Minimalist 2D vector-art webcomic-style illustration of a large, official-looking document with a glowing stamp that says Truman Doctrine. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Official, historic. Action: Static document with a stamp."),
    ("frame_40", "Minimalist 2D vector-art webcomic-style illustration of a parachute dropping a crate full of money and weapons to a small, worried cartoon country figure. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Helpful, militaristic. Action: Crate dropping on a parachute."),

    ("frame_41", "Minimalist 2D vector-art webcomic-style illustration of a giant sack of coins with an American flag pouring money over broken European buildings, fixing them. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, bright lighting. Mood: Rebuilding, prosperous. Action: Money repairing buildings."),
    ("frame_42", "Minimalist 2D vector-art webcomic-style illustration of a Soviet character crossing his arms and stubbornly turning his head away from a pile of gold coins. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Stubborn, suspicious. Action: Character refusing a gift."),
    ("frame_43", "Minimalist 2D vector-art webcomic-style illustration of gold coins turning into iron chains wrapping around a cartoon figure's wrists. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, dark lighting. Mood: Paranoid, sinister. Action: Coins morphing into chains."),
    ("frame_44", "Minimalist 2D vector-art webcomic-style illustration of two angry crowds facing each other across a thick black line painted on the ground. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Hostile, divided. Action: Two groups glaring at each other."),
    ("frame_45", "Minimalist 2D vector-art webcomic-style illustration of a giant glowing white thumbs-up icon with the text 7000 next to it. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, bright lighting. Mood: Engaging, promotional. Action: Like button glowing."),
    ("frame_46", "Minimalist 2D vector-art webcomic-style illustration of a cartoon missile flying dangerously close to a ticking pocket watch. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, tense lighting. Mood: Apocalyptic, suspenseful. Action: Missile hovering near a clock."),
    ("frame_47", "Minimalist 2D vector-art webcomic-style illustration of a thermometer exploding with red liquid over a sign that says Berlin. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Explosive, tense. Action: Thermometer shattering."),
    ("frame_48", "Minimalist 2D vector-art webcomic-style illustration of a map of Germany sliced into four brightly colored puzzle pieces. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Analytical. Action: Map separating into puzzle pieces."),
    ("frame_49", "Minimalist 2D vector-art webcomic-style illustration of three cartoon hands pushing puzzle pieces together and placing a shiny new coin on top. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Cooperative, economic. Action: Hands combining pieces and a coin."),
    ("frame_50", "Minimalist 2D vector-art webcomic-style illustration of an exaggerated cartoon Stalin placing giant red STOP signs and barbed wire across a highway. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Aggressive, restrictive. Action: Character blocking a road."),

    ("frame_51", "Minimalist 2D vector-art webcomic-style illustration of a small cartoon city trapped inside a glass jar with the lid screwed on tight. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, claustrophobic lighting. Mood: Trapped, isolated. Action: City inside a sealed jar."),
    ("frame_52", "Minimalist 2D vector-art webcomic-style illustration of a cartoon airplane flying over a brick wall, carrying a large bundle on a rope. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, hopeful lighting. Mood: Heroic, problem-solving. Action: Airplane flying over a blockade."),
    ("frame_53", "Minimalist 2D vector-art webcomic-style illustration of an endless line of cartoon airplanes dropping boxes of bread and lumps of coal into a city. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Relentless, supportive. Action: Airplanes dropping supplies in a loop."),
    ("frame_54", "Minimalist 2D vector-art webcomic-style illustration of a cartoon bear angrily pulling away barbed wire, revealing a solid brick wall permanently splitting a map. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Resigned, divided. Action: Bear removing wire but a wall remains."),
    ("frame_55", "Minimalist 2D vector-art webcomic-style illustration of two distinct flags (West Germany and East Germany) planted on opposite sides of a deep crack in the ground. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Formal, divided. Action: Flags standing on separate ground."),
    ("frame_56", "Minimalist 2D vector-art webcomic-style illustration of several worried cartoon characters huddling together and looking nervously at a dark shadow. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, gloomy lighting. Mood: Fearful, united. Action: Characters huddling together."),
    ("frame_57", "Minimalist 2D vector-art webcomic-style illustration of a massive blue shield with the NATO compass emblem slamming into the ground. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, strong lighting. Mood: Powerful, escalated. Action: Shield slamming into the earth."),
    ("frame_58", "Minimalist 2D vector-art webcomic-style illustration of a calendar page showing August 1949 catching on fire. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, dramatic lighting. Mood: Tense, critical. Action: Calendar page burning."),
    ("frame_59", "Minimalist 2D vector-art webcomic-style illustration of a giant mushroom cloud with a red star on it, while an American character drops his jaw in shock. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, bright flash lighting. Mood: Shocking, game-changing. Action: Mushroom cloud erupting and character reacting."),
    ("frame_60", "Minimalist 2D vector-art webcomic-style illustration of two cartoon figures frantically stacking towering, precarious piles of missiles on their respective sides. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Frantic, dangerous. Action: Characters aggressively stacking missiles."),

    ("frame_61", "Minimalist 2D vector-art webcomic-style illustration of the Earth with a cartoon skull face, completely surrounded by dozens of pointed missiles. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, dark lighting. Mood: Fatalistic, doomed. Action: Missiles pointing at a skull Earth."),
    ("frame_62", "Minimalist 2D vector-art webcomic-style illustration of two characters holding guns to each other's heads, both sweating profusely and too afraid to pull the trigger. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, tense lighting. Mood: Paralyzed by fear. Action: Standoff with guns."),
    ("frame_63", "Minimalist 2D vector-art webcomic-style illustration of a world map covered in numerous small explosions and crossed swords icons. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Chaotic, destructive. Action: Explosions popping up on a map."),
    ("frame_64", "Minimalist 2D vector-art webcomic-style illustration of three separate polaroid photos showing simplified cartoon soldiers fighting in different environments (snow, jungle, mountains). Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Historical, grim. Action: Photos scattered on a surface."),
    ("frame_65", "Minimalist 2D vector-art webcomic-style illustration of a delicate glass globe balancing precariously on the edge of a table. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Fragile, cautionary. Action: Globe teetering on an edge."),
    ("frame_66", "Minimalist 2D vector-art webcomic-style illustration of a bridge collapsing in the middle because two people on opposite ends are pulling it apart. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Destructive, tragic. Action: Bridge breaking in half."),
    ("frame_67", "Minimalist 2D vector-art webcomic-style illustration of the cynical host character waving goodbye while holding a Like and Subscribe sign. Thick black outlines, flat colors. Camera Angle: Medium shot. Lighting: Flat, even lighting. Mood: Friendly, final. Action: Host waving to the camera."),
    ("frame_68", "Minimalist 2D vector-art webcomic-style illustration of a scrolling list of cartoon avatars on a screen next to the host. Thick black outlines, flat colors. Camera Angle: Wide shot. Lighting: Flat, even lighting. Mood: Grateful, promotional. Action: Names scrolling on a screen."),
    ("frame_69", "Minimalist 2D vector-art webcomic-style illustration of a glowing Boosty logo with an arrow pointing down to it. Thick black outlines, flat colors. Camera Angle: Close-up. Lighting: Flat, even lighting. Mood: Direct action. Action: Arrow pointing down to the logo."),
]


# ============ GENERATION LOGIC ============

def generate_image(prompt: str, filename: str) -> dict:
    """Submit a text-to-image job to Fooocus-API."""
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "style_selections": [STYLE],
        "performance_selection": PERFORMANCE,
        "aspect_ratios_selection": ASPECT_RATIO,
        "image_number": 1,
        "image_seed": -1,  # random
        "sharpness": SHARPNESS,
        "guidance_scale": GUIDANCE_SCALE,
        "base_model_name": "juggernautXL_v8Rundiffusion.safetensors",
        "refiner_model_name": "None",
        "refiner_switch": 0.5,
        "loras": [
            {
                "model_name": "None",
                "weight": 1.0
            }
        ],
        "advanced_params": {
            "disable_preview": True,
            "adm_scaler_positive": 1.5,
            "adm_scaler_negative": 0.8,
            "adm_scaler_end": 0.3,
            "adaptive_cfg": 7.0,
            "sampler_name": "dpmpp_2m_sde_gpu",
            "scheduler_name": "karras",
            "overwrite_step": STEPS,
            "overwrite_switch": -1,
            "overwrite_width": -1,
            "overwrite_height": -1,
        },
        "require_base64": False,
        "async_process": True,
    }

    headers = {"Content-Type": "application/json", "accept": "application/json"}
    resp = requests.post(
        f"{FOOOCUS_HOST}{TEXT2IMG_ENDPOINT}",
        json=payload,
        headers=headers,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()


def wait_for_job(job_id: str, timeout: int = 300) -> dict:
    """Poll until the job is done."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{FOOOCUS_HOST}{QUERY_JOB_ENDPOINT}",
            params={"job_id": job_id, "require_step_preview": False},
            timeout=10
        )
        data = resp.json()
        status = data.get("job_stage", "UNKNOWN")
        
        if status == "SUCCESS":
            return data
        elif status in ("FAILED", "ERROR"):
            print(f"  [ERROR] Job {job_id} failed: {data}")
            return data
        
        time.sleep(3)
    
    print(f"  [TIMEOUT] Job {job_id} timed out after {timeout}s")
    return {}


def download_image(url: str, save_path: str):
    """Download image from Fooocus temp storage."""
    # If url is relative, prepend host
    if url.startswith("/"):
        url = f"{FOOOCUS_HOST}{url}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(resp.content)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total = len(PROMPTS)
    print(f"{'='*60}")
    print(f"  FOOOCUS BATCH GENERATOR - {total} frames")
    print(f"  Output: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Host: {FOOOCUS_HOST}")
    print(f"{'='*60}\n")
    
    # Check connection
    try:
        r = requests.get(f"{FOOOCUS_HOST}/v1/generation/job-queue", timeout=5)
        print("[OK] Connected to Fooocus-API\n")
    except Exception as e:
        print(f"[ERROR] Cannot connect to Fooocus-API at {FOOOCUS_HOST}")
        print(f"  Make sure Fooocus-API is running!")
        print(f"  Error: {e}")
        sys.exit(1)
    
    failed = []
    
    for i, (name, prompt) in enumerate(PROMPTS, 1):
        print(f"[{i}/{total}] Generating: {name}")
        print(f"  Prompt: {prompt[:80]}...")
        
        try:
            result = generate_image(prompt, name)
            job_id = result.get("job_id")
            
            if not job_id:
                print(f"  [ERROR] No job_id returned: {result}")
                failed.append(name)
                continue
            
            print(f"  Job ID: {job_id} - waiting...")
            job_result = wait_for_job(job_id)
            
            if job_result.get("job_stage") == "SUCCESS":
                # Get image URL from result
                imgs = job_result.get("job_result", [])
                if imgs:
                    img_url = imgs[0].get("url", "")
                    save_path = os.path.join(OUTPUT_DIR, f"{name}.png")
                    download_image(img_url, save_path)
                    print(f"  [SAVED] {save_path}")
                else:
                    print(f"  [WARN] No images in result")
                    failed.append(name)
            else:
                failed.append(name)
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed.append(name)
        
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  DONE! Generated: {total - len(failed)}/{total}")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print(f"  Output folder: {os.path.abspath(OUTPUT_DIR)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
