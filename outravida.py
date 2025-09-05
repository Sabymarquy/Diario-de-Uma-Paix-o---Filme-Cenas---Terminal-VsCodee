import time
import sys
import os
import threading
import random

# --- CONSTANTES ANSI (Cores e Comandos para o Terminal) ---
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# --- CORES PERSONALIZADAS ---
NOAH_COLOR = "\033[38;5;120m" # Verde claro para a fala do Noah
ALLIE_COLOR = "\033[38;5;210m"  # Rosa/vermelho mais claro para a fala da Allie
INFO_COLOR = "\033[38;5;248m"   # Cinza claro para Título/Identificador (INFO)
INACTIVE_LYRIC_COLOR = "\033[38;5;242m" # Cinza médio/escuro para a linha inativa

# --- NEBULA_COLORS e NEBULA_CHAR ---
# Usando tons de cinza/branco para a nébula
NEBULA_COLORS = [
    "\033[38;5;231m", # Branco
    "\033[38;5;252m", # Cinza claro
    "\033[38;5;248m", # Cinza médio
    "\033[38;5;244m", # Cinza um pouco mais escuro
    "\033[38;5;239m", # Cinza escuro
]
NEBULA_CHAR = "•" # Caractere de ponto para a nébula

# --- FUNÇÕES ANSI ---
CURSOR_POS = lambda row, col: f"\033[{row};{col}H"
CLEAR_SCREEN = "\033[H\033[J"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

# --- VARIÁVEIS GLOBAIS ---
terminal_width = 80
terminal_height = 24 

# Configurações da caixa de exibição
BOX_WIDTH = 60
BOX_HEIGHT = 12 

# Posição da caixa no terminal (centralizada verticalmente)
BOX_START_COL = 2 
BOX_START_ROW = (terminal_height - BOX_HEIGHT) // 2 

# Variáveis da Névoa
NEBULA_DENSITY = 0.003 # Densidade da névoa (pode ajustar)
NEBULA_UPDATE_INTERVAL = 0.1 # Frequência de atualização
NEBULA_LIFESPAN = 1.0 # Quanto tempo um ponto de névoa permanece visível

stop_background_animation = False # Controla o loop da thread de background
background_animation_thread = None # Referência à thread de background

screen_lock = threading.Lock() # Para sincronizar acesso ao terminal

active_nebula_pixels = {} # Armazena pixels ativos da névoa (posição: (timestamp, char original))

# --- FUNÇÃO PARA AJUSTAR O TEXTO À LARGURA DA CAIXA (AGORA RESPEITA \n) ---
def split_and_wrap_text(text, max_width):
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        words = line.split()
        current_line = []
        current_line_length = 0

        for word in words:
            if current_line_length + len(word) + (1 if current_line else 0) <= max_width:
                current_line.append(word)
                current_line_length += len(word) + (1 if current_line else 0) 
            else:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_line_length = len(word)
                
        if current_line:
            wrapped_lines.append(" ".join(current_line))
    return wrapped_lines

# --- FUNÇÃO PARA EXIBIR A TELA INICIAL ---
def display_initial_setup_screen():
    sys.stdout.write(CLEAR_SCREEN)
    sys.stdout.write(f"{CURSOR_POS(1, 2)}{BOLD}{INFO_COLOR}[SYSTEM]{RESET} Inicializando módulos para Exibição de Conteúdo...\n")
    sys.stdout.write(f"{CURSOR_POS(2, 2)}{INFO_COLOR}[STATUS]{RESET} Preparando exibição das linhas...\n")
    sys.stdout.write(f"{CURSOR_POS(3, 2)}{INFO_COLOR}[STATUS]{RESET} Verificando tamanho do terminal...\n")
    sys.stdout.flush()
    time.sleep(2.0)
    sys.stdout.write(CLEAR_SCREEN)
    sys.stdout.flush()

# --- FUNÇÃO DA ANIMAÇÃO DE FUNDO (NÉVOA) ---
def animate_nebula_background():
    global stop_background_animation, terminal_width, terminal_height, screen_lock, active_nebula_pixels
    global BOX_START_ROW, BOX_START_COL, BOX_HEIGHT, BOX_WIDTH, NEBULA_CHAR, NEBULA_COLORS

    MARGIN = 1 
    
    while not stop_background_animation:
        current_time = time.monotonic()
        
        with screen_lock:
            pixels_to_remove = []
            for (row, col), (timestamp_activated, original_char) in list(active_nebula_pixels.items()):
                if current_time - timestamp_activated > NEBULA_LIFESPAN:
                    sys.stdout.write(CURSOR_POS(row + 1, col + 1) + " ") 
                    pixels_to_remove.append((row, col))
            for p in pixels_to_remove:
                del active_nebula_pixels[p]

            for _ in range(int(terminal_width * terminal_height * NEBULA_DENSITY)):
                row = random.randint(0, terminal_height - 1)
                col = random.randint(0, terminal_width - 1) 
                
                is_in_lyrics_box_area = \
                    (BOX_START_ROW - MARGIN <= row < BOX_START_ROW + BOX_HEIGHT + MARGIN) and \
                    (BOX_START_COL - MARGIN <= col < BOX_START_COL + BOX_WIDTH + MARGIN)
                
                if not is_in_lyrics_box_area:
                    sys.stdout.write(CURSOR_POS(row + 1, col + 1)) 
                    color = random.choice(NEBULA_COLORS)
                    sys.stdout.write(f"{color}{NEBULA_CHAR}{RESET}")
                    active_nebula_pixels[(row, col)] = (current_time, " ") 
            sys.stdout.flush()
        
        time.sleep(NEBULA_UPDATE_INTERVAL)

# --- FUNÇÃO PRINCIPAL: Display das Linhas no Estilo Spotify ---
def display_spotify_lyrics(current_line_index, lyrics_data, content_info): 
    global terminal_width, terminal_height, BOX_WIDTH, BOX_HEIGHT, BOX_START_ROW, BOX_START_COL

    with screen_lock:
        try:
            current_term_width, current_term_height = os.get_terminal_size()
            
            min_required_height = BOX_HEIGHT + 2 
            terminal_height = max(min_required_height, current_term_height)
            terminal_width = max(80, current_term_width) 

            BOX_START_COL = 2 
            BOX_START_ROW = (terminal_height - BOX_HEIGHT) // 2 
            if BOX_START_ROW < 1: BOX_START_ROW = 1 

        except OSError:
            pass 

        for r in range(BOX_HEIGHT):
            sys.stdout.write(CURSOR_POS(BOX_START_ROW + r + 1, BOX_START_COL + 1) + " " * BOX_WIDTH)

        current_display_row = 0
        
        for title_part_line in content_info["title_lines"]:
            title_wrapped = split_and_wrap_text(title_part_line, BOX_WIDTH - 4)
            for line in title_wrapped: 
                if current_display_row < BOX_HEIGHT:
                    sys.stdout.write(CURSOR_POS(BOX_START_ROW + current_display_row + 1, BOX_START_COL + 2)) 
                    sys.stdout.write(f"{BOLD}{INFO_COLOR}{line}{RESET}") 
                    current_display_row += 1
        
        for info_part_line in content_info["artist_lines"]: 
            info_wrapped = split_and_wrap_text(info_part_line, BOX_WIDTH - 4)
            for line in info_wrapped: 
                if current_display_row < BOX_HEIGHT:
                    sys.stdout.write(CURSOR_POS(BOX_START_ROW + current_display_row + 1, BOX_START_COL + 2))
                    sys.stdout.write(f"{INFO_COLOR}{line}{RESET}")
                    current_display_row += 1
        
        if current_display_row < BOX_HEIGHT:
            current_display_row += 1

        lyrics_lines_to_show = []
        
        LYRIC_WRAP_WIDTH = BOX_WIDTH - 4 

        lines_before_active = 2 
        lines_after_active = BOX_HEIGHT - current_display_row - lines_before_active - 1 

        for i in range(current_line_index - lines_before_active, current_line_index):
            if i >= 0:
                wrapped_lines = split_and_wrap_text(lyrics_data[i]["original"], LYRIC_WRAP_WIDTH)
                for line in wrapped_lines:
                    lyrics_lines_to_show.append({"text": line, "color": DIM + INACTIVE_LYRIC_COLOR})
            else:
                lyrics_lines_to_show.append({"text": "", "color": ""})

        if current_line_index < len(lyrics_data):
            wrapped_lines = split_and_wrap_text(lyrics_data[current_line_index]["original"], LYRIC_WRAP_WIDTH)
            for line in wrapped_lines:
                lyrics_lines_to_show.append({"text": line, "color": BOLD + lyrics_data[current_line_index]["color"]})
        else:
            lyrics_lines_to_show.append({"text": "", "color": ""})

        for i in range(current_line_index + 1, current_line_index + 1 + lines_after_active):
            if i < len(lyrics_data):
                wrapped_lines = split_and_wrap_text(lyrics_data[i]["original"], LYRIC_WRAP_WIDTH)
                for line in wrapped_lines:
                    lyrics_lines_to_show.append({"text": line, "color": DIM + INACTIVE_LYRIC_COLOR})
            else:
                lyrics_lines_to_show.append({"text": "", "color": ""})

        for i, line_data in enumerate(lyrics_lines_to_show):
            if current_display_row < BOX_HEIGHT:
                current_col_pos = BOX_START_COL + 2 
                sys.stdout.write(CURSOR_POS(BOX_START_ROW + current_display_row + 1, current_col_pos))
                sys.stdout.write(f"{line_data['color']}{line_data['text']}{RESET}") 
                current_display_row += 1
            else:
                break 

        sys.stdout.flush()

# --- FUNÇÃO PARA LIMPAR TODOS OS PIXELS DE ANIMAÇÃO VISÍVEIS ---
def clear_all_background_animations():
    global active_nebula_pixels, screen_lock

    with screen_lock:
        for pos, pixel_info in list(active_nebula_pixels.items()):
            row_0based, col_0based = pos
            sys.stdout.write(CURSOR_POS(row_0based + 1, col_0based + 1) + " ") 
        active_nebula_pixels.clear() 
        sys.stdout.flush()

# --- DADOS DO CONTEÚDO ---
CONTENT_INFO = { 
    "title_lines": [  
        "Cena: Diário de uma Paixão"
    ],
    "artist_lines": [ 
        "..." 
    ]
}

# Linhas da música e seus tempos (estimados)
LYRICS_DATA = [
    {"time": 0.0, "original": "Minha querida Allie", "color": NOAH_COLOR},
    {"time": 3.0, "original": "Não consegui dormir ontem", "color": NOAH_COLOR},
    {"time": 4.0, "original": "Porque sei que está \nacabado entre nós", "color": NOAH_COLOR},
    {"time": 10.0, "original": "Não estou mais triste", "color": NOAH_COLOR},
    {"time": 11.0, "original": "Porque sei que o que\ntivemos foi verdadeiro", "color": NOAH_COLOR},
    {"time": 15.0, "original": "E se em algum lugar\ndistante no futuro", "color": NOAH_COLOR},
    {"time": 17.0, "original": "Nos encontrarmos novamente\nem nossas novas vidas", "color": NOAH_COLOR},
    {"time": 21.0, "original": "Vou sorrir pra você\ncom alegria", "color": NOAH_COLOR},
    {"time": 24.0, "original": "E lembrarei como passamos um\nverão embaixo das árvores", "color": NOAH_COLOR},
    {"time": 30.0, "original": "Aprendendo um com o outro\ne nos apaixonando", "color": NOAH_COLOR},
    {"time": 39.0, "original": "Não me conhece, mas eu\nme conheço", "color": NOAH_COLOR},
    {"time": 43.0, "original": "E quando vejo algo de que\ngosto, eu fico.. eu adoro", "color": NOAH_COLOR},
    {"time": 50.0, "original": "Eu fico louco\ncompletamente", "color": NOAH_COLOR},
    {"time": 52.0, "original": "Do que ta falando?", "color": ALLIE_COLOR},
    {"time": 54.0, "original": "Ué, de você!", "color": NOAH_COLOR},
    {"time": 58.0, "original": "--- Só em outra vida mesmo... ---", "type": "end_of_song", "color": INFO_COLOR}
]

# Duração total da música (baseada nos tempos estimados)
TOTAL_MUSIC_DURATION = 62.0

# --- FUNÇÃO PRINCIPAL PARA A ANIMAÇÃO ---
def start_lyrics_animation():
    global stop_background_animation, background_animation_thread

    sys.stdout.write(HIDE_CURSOR) 
    sys.stdout.write(CLEAR_SCREEN) 
    sys.stdout.flush()

    stop_background_animation = False
    background_animation_thread = threading.Thread(target=animate_nebula_background) 
    background_animation_thread.daemon = True 
    background_animation_thread.start()

    start_time = time.monotonic() 
    current_line_index = 0 
    
    while time.monotonic() - start_time < TOTAL_MUSIC_DURATION:
        elapsed_time = time.monotonic() - start_time 
        
        while current_line_index < len(LYRICS_DATA) and elapsed_time >= LYRICS_DATA[current_line_index]["time"]:
            current_line_index += 1
        
        try:
            display_index_for_display = current_line_index - 1 
            if display_index_for_display < 0 and LYRICS_DATA[0]["time"] == 0.0:
                display_index_for_display = 0 

            if display_index_for_display >= len(LYRICS_DATA):
                display_index_for_display = len(LYRICS_DATA) - 1 

            display_spotify_lyrics(display_index_for_display, LYRICS_DATA, CONTENT_INFO) 

        except OSError:
            pass 

        next_target_time = TOTAL_MUSIC_DURATION
        if current_line_index < len(LYRICS_DATA):
            next_target_time = LYRICS_DATA[current_line_index]["time"]
        
        time_to_sleep = next_target_time - (time.monotonic() - start_time)
        
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

    stop_background_animation = True 
    if background_animation_thread and background_animation_thread.is_alive():
        background_animation_thread.join(timeout=1) 

    clear_all_background_animations()

    with screen_lock:
        sys.stdout.write(CLEAR_SCREEN)
        
        final_message = "CENA ENCERRADA" 
        final_message_col = (terminal_width - len(final_message) - len(BOLD) - len(INFO_COLOR) - len(RESET)) // 2
        final_message_row = terminal_height // 2
        
        sys.stdout.write(f"{CURSOR_POS(final_message_row, final_message_col)}{BOLD}{INFO_COLOR}{final_message}{RESET}\n")
        sys.stdout.write(f"{CURSOR_POS(final_message_row + 1, (terminal_width - len('Obrigado por assistir!') - len(INFO_COLOR) - len(RESET)) // 2)}{INFO_COLOR}Obrigado por assistir!{RESET}\n")
        sys.stdout.flush()
    
    time.sleep(3)

if __name__ == "__main__":
    try:
        display_initial_setup_screen()
        start_lyrics_animation()
        
        with screen_lock:
            sys.stdout.write(CLEAR_SCREEN)
            sys.stdout.write(CURSOR_POS(terminal_height // 2 - 1, (terminal_width - len("Programa finalizado. Pressione Enter para sair.")) // 2))
            sys.stdout.write("Programa finalizado. Pressione Enter para sair.\n")
            sys.stdout.flush()
        
        input()
    except KeyboardInterrupt:
        print("\nExibição interrompida pelo usuário.")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
    finally:
        stop_background_animation = True
        if background_animation_thread and background_animation_thread.is_alive():
            background_animation_thread.join(timeout=1)
        clear_all_background_animations()
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()