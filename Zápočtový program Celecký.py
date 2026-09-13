import math
import random

BOARD_SIZE = 15
EMPTY = '.'
PLAYER_X = 'X'
PLAYER_O = 'O'

WIN_FLAG = 100000000
FOUR_FLAG = 1000000
SCORE_OPEN_4 = 20000
SCORE_CLOSED_4 = 200
SCORE_OPEN_3 = 1500
SCORE_CLOSED_3 = 50
SCORE_OPEN_2 = 300
SCORE_CLOSED_2 = 10

random.seed(42)
ZOBRIST_TABLE = [[[random.getrandbits(64) for _ in range(2)] for _ in range(15)] for _ in range(15)]

class InteractiveGomokuEngine:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.board = [[EMPTY for _ in range(size)] for _ in range(size)]
        self.directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        self.axes_X = [[[0, 0, 0, 0] for _ in range(size)] for _ in range(size)]
        self.axes_O = [[[0, 0, 0, 0] for _ in range(size)] for _ in range(size)]
        self.total_X_atk = [[0 for _ in range(size)] for _ in range(size)]
        self.total_O_atk = [[0 for _ in range(size)] for _ in range(size)]

        self.history = []
        self.current_hash = 0
        self.tt = {}
        self.reset_board()

    def reset_board(self):
        self.board = [[EMPTY for _ in range(self.size)] for _ in range(self.size)]
        self.history.clear()
        self.tt.clear()
        self.current_hash = 0
        for r in range(self.size):
            for c in range(self.size):
                self._full_reeval_cell(r, c)

    def print_board(self):
        print("\n    " + " ".join(f"{c:2d}" for c in range(self.size)))
        print("   +" + "---" * self.size + "+")
        for r in range(self.size):
            row_str = f"{r:2d} |"
            for c in range(self.size):
                row_str += f" {self.board[r][c]} "
            row_str += "|"
            print(row_str)
        print("   +" + "---" * self.size + "+\n")

    def get_player_idx(self, player):
        return 0 if player == PLAYER_X else 1

    def combine_axes(self, axes):
        return sum(axes)

    def _evaluate_single_axis(self, r, c, axis_idx, player):
        dr, dc = self.directions[axis_idx]
        opponent = PLAYER_O if player == PLAYER_X else PLAYER_X

        opp_bonus = sum(5 for step_dir in [1, -1] 
                        if 0 <= r + step_dir * dr < self.size and 0 <= c + step_dir * dc < self.size 
                        and self.board[r + step_dir * dr][c + step_dir * dc] == opponent)

        pos_limit, neg_limit = 0, 0
        for i in range(1, 5):
            nr, nc = r + i * dr, c + i * dc
            if not (0 <= nr < self.size and 0 <= nc < self.size) or self.board[nr][nc] == opponent: break
            pos_limit = i
        for i in range(1, 5):
            nr, nc = r - i * dr, c - i * dc
            if not (0 <= nr < self.size and 0 <= nc < self.size) or self.board[nr][nc] == opponent: break
            neg_limit = i

        axis_score = opp_bonus
        for start_offset in range(5):
            min_offset, max_offset = -start_offset, 4 - start_offset
            if min_offset >= -neg_limit and max_offset <= pos_limit:
                stones_count = 1
                valid = True
                for offset in range(5):
                    if offset == start_offset: continue
                    val = self.board[r + (min_offset + offset) * dr][c + (min_offset + offset) * dc]
                    if val == player: stones_count += 1
                    elif val == opponent: valid = False; break

                if valid:
                    left_open = (min_offset - 1 >= -neg_limit)
                    right_open = (max_offset + 1 <= pos_limit)
                    
                    if left_open and self.board[r + (min_offset - 1) * dr][c + (min_offset - 1) * dc] == player: valid = False
                    if right_open and self.board[r + (max_offset + 1) * dr][c + (max_offset + 1) * dc] == player: valid = False

                if valid:
                    is_open = left_open and right_open
                    is_half = left_open or right_open
                    missing = 5 - stones_count

                    if missing == 0: return WIN_FLAG
                    elif missing == 1:
                        if is_open: axis_score += FOUR_FLAG + SCORE_OPEN_4
                        elif is_half: axis_score += FOUR_FLAG + SCORE_CLOSED_4
                    elif missing == 2:
                        if is_open: axis_score += SCORE_OPEN_3
                        elif is_half: axis_score += SCORE_CLOSED_3
                    elif missing == 3:
                        if is_open: axis_score += SCORE_OPEN_2
                        elif is_half: axis_score += SCORE_CLOSED_2
                    else:
                        if is_open: axis_score += 1
                        else: axis_score += 0
        return axis_score

    def _full_reeval_cell(self, r, c):
        if self.board[r][c] != EMPTY:
            self.axes_X[r][c] = self.axes_O[r][c] = [0, 0, 0, 0]
            self.total_X_atk[r][c] = self.total_O_atk[r][c] = 0
            return
        for d in range(4):
            self.axes_X[r][c][d] = self._evaluate_single_axis(r, c, d, PLAYER_X)
            self.axes_O[r][c][d] = self._evaluate_single_axis(r, c, d, PLAYER_O)
        self.total_X_atk[r][c] = self.combine_axes(self.axes_X[r][c])
        self.total_O_atk[r][c] = self.combine_axes(self.axes_O[r][c])

    def make_move(self, r, c, player):
        old_state = {}
        self.board[r][c] = player
        self.current_hash ^= ZOBRIST_TABLE[r][c][self.get_player_idx(player)]
        old_state[(r, c)] = (list(self.axes_X[r][c]), list(self.axes_O[r][c]), self.total_X_atk[r][c], self.total_O_atk[r][c])
        self.total_X_atk[r][c] = self.total_O_atk[r][c] = 0

        for d in range(4):
            dr, dc = self.directions[d]
            for step in range(-4, 5):
                if step == 0: continue
                nr, nc = r + step * dr, c + step * dc
                if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == EMPTY:
                    if (nr, nc) not in old_state:
                        old_state[(nr, nc)] = (list(self.axes_X[nr][nc]), list(self.axes_O[nr][nc]), self.total_X_atk[nr][nc], self.total_O_atk[nr][nc])
                    self.axes_X[nr][nc][d] = self._evaluate_single_axis(nr, nc, d, PLAYER_X)
                    self.axes_O[nr][nc][d] = self._evaluate_single_axis(nr, nc, d, PLAYER_O)
                    self.total_X_atk[nr][nc] = self.combine_axes(self.axes_X[nr][nc])
                    self.total_O_atk[nr][nc] = self.combine_axes(self.axes_O[nr][nc])

        self.history.append((r, c, old_state))

    def undo_move(self):
        r, c, old_state = self.history.pop()
        player = self.board[r][c]
        self.current_hash ^= ZOBRIST_TABLE[r][c][self.get_player_idx(player)]
        self.board[r][c] = EMPTY
        for (nr, nc), (ax_x, ax_o, tot_x, tot_o) in old_state.items():
            self.axes_X[nr][nc], self.axes_O[nr][nc] = ax_x, ax_o
            self.total_X_atk[nr][nc], self.total_O_atk[nr][nc] = tot_x, tot_o

    def undo_last_full_turn(self):
        if len(self.history) >= 2:
            self.undo_move()
            self.undo_move()
            return True
        return False

    def solve_vcf(self, player, depth, max_depth=4):
        if depth >= max_depth: return None
        opp = PLAYER_O if player == PLAYER_X else PLAYER_X
        m_atk = self.total_X_atk if player == PLAYER_X else self.total_O_atk

        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == EMPTY and m_atk[r][c] >= WIN_FLAG:
                    return [(r, c)]

        forcing = [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == EMPTY and m_atk[r][c] >= FOUR_FLAG]
        if not forcing:
            return None
        forcing.sort(key=lambda m: m_atk[m[0]][m[1]], reverse=True)

        for r, c in forcing:
            self.make_move(r, c, player)
            o_atk = self.total_X_atk if opp == PLAYER_O else self.total_O_atk
            blocks = [(br, bc) for br in range(self.size) for bc in range(self.size) if self.board[br][bc] == EMPTY and o_atk[br][bc] >= WIN_FLAG]

            if not blocks:
                self.undo_move()
                return [(r, c)]

            path = None
            for br, bc in blocks:
                self.make_move(br, bc, opp)
                sub = self.solve_vcf(player, depth + 2, max_depth)
                self.undo_move()
                if not sub:
                    path = None
                    break
                else:
                    path = [(r, c)] + sub
            self.undo_move()
            if path: return path
        return None

    def get_candidates(self, player, limit=6):
        my_atk = self.total_X_atk if player == PLAYER_X else self.total_O_atk
        opp_atk = self.total_O_atk if player == PLAYER_X else self.total_X_atk
        wins, opp_wins, normals = [], [], []

        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == EMPTY:
                    a, d = my_atk[r][c], opp_atk[r][c]
                    if a >= WIN_FLAG: wins.append((r, c))
                    elif d >= WIN_FLAG: opp_wins.append((r, c))
                    elif a + d > 0: normals.append(((a % FOUR_FLAG) + 0.9 * (d % FOUR_FLAG), r, c))

        if wins: return [wins[0]]
        if opp_wins: return opp_wins

        opp = PLAYER_O if player == PLAYER_X else PLAYER_X
        my_vcf = self.solve_vcf(player, 0, max_depth=4)
        if my_vcf: return [my_vcf[0]]
        
        opp_vcf = self.solve_vcf(opp, 0, max_depth=4)
        if opp_vcf: return [opp_vcf[0]]

        normals.sort(key=lambda x: x[0], reverse=True)
        return [(r, c) for _, r, c in normals[:limit]]

    def check_five(self, player):
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == player:
                    for dr, dc in self.directions:
                        cnt = 1
                        for step in range(1, 6):
                            nr, nc = r + step * dr, c + step * dc
                            if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == player: cnt += 1
                            else: break
                        if cnt == 5 and not (0 <= r - dr < self.size and 0 <= c - dc < self.size and self.board[r - dr][c - dc] == player):
                            return True
        return False

    def alpha_beta(self, depth, max_depth, alpha, beta, is_max, current_player):
        opp = PLAYER_O if current_player == PLAYER_X else PLAYER_X
        if self.check_five(current_player): return WIN_FLAG - depth
        if self.check_five(opp): return -WIN_FLAG + depth
        
        if depth >= max_depth:
            p_moves = self.get_candidates(current_player, limit=3)
            o_moves = self.get_candidates(opp, limit=3)
            p_sc = sum((self.total_X_atk[r][c] % FOUR_FLAG) + (self.total_O_atk[r][c] % FOUR_FLAG) for r, c in p_moves)
            o_sc = sum((self.total_O_atk[r][c] % FOUR_FLAG) + (self.total_X_atk[r][c] % FOUR_FLAG) for r, c in o_moves)
            return p_sc - o_sc

        candidates = self.get_candidates(current_player if is_max else opp, limit=5)
        if not candidates: return 0

        best_score = -math.inf if is_max else math.inf
        best_move = candidates[0]

        for r, c in candidates:
            self.make_move(r, c, current_player if is_max else opp)
            score = self.alpha_beta(depth + 1, max_depth, alpha, beta, not is_max, current_player)
            self.undo_move()

            if is_max and score > best_score: best_score, best_move = score, (r, c)
            elif not is_max and score < best_score: best_score, best_move = score, (r, c)

            if is_max: alpha = max(alpha, best_score)
            else: beta = min(beta, best_score)
            if beta <= alpha: break

        self.tt[self.current_hash] = (max_depth - depth, best_score, 0, best_move)
        return best_score

    def get_best_move(self, player, thinking_depth=6):
        vcf_path = self.solve_vcf(player, 0, max_depth=10)
        if vcf_path:
            return vcf_path[0]
        
        self.tt.clear()
        self.alpha_beta(0, thinking_depth, -math.inf, math.inf, True, player)
        
        if self.current_hash in self.tt and self.tt[self.current_hash][3]:
            return self.tt[self.current_hash][3]
        
        cands = self.get_candidates(player, limit=1)
        if cands:
            return cands[0]
        return None

    def calculate_difficulty(self, path, winner, start_player):
        diff, curr = 0, start_player
        for move in path:
            if curr == winner:
                cands = self.get_candidates(curr, limit=10)
                rank = next((i for i, (r, c) in enumerate(cands) if r == move[0] and c == move[1]), 99)
                
                min_d = 99
                for rr in range(self.size):
                    for cc in range(self.size):
                        if self.board[rr][cc] != EMPTY:
                            d = max(abs(rr - move[0]), abs(cc - move[1]))
                            if d < min_d: min_d = d
                
                if rank == 0: pass
                elif rank in [1, 2]: diff += 3
                else: diff += 10
                
                if min_d == 2: diff += 1
                elif min_d > 2: diff += 2
                
            self.make_move(move[0], move[1], curr)
            curr = PLAYER_O if curr == PLAYER_X else PLAYER_X
            
        for _ in path: self.undo_move()
        return diff

    def run_progressive_search(self, start_player, thinking_depth=6, max_steps=30):
        print(f"\nSimuluji vývoj hry... (Hloubka přemýšlení: {thinking_depth}, Max tahů: {max_steps})")
        path = []
        curr_player = start_player
        winner = None

        for step in range(max_steps):
            best_move = self.get_best_move(curr_player, thinking_depth)
            if not best_move: break

            path.append(best_move)
            self.make_move(best_move[0], best_move[1], curr_player)

            print(f"Tah {step + 1}: Hráč {curr_player} zahrál na souřadnice [{best_move[0]}, {best_move[1]}]")
            self.print_board()
            
            if self.check_five(curr_player):
                winner = curr_player
                break
                
            curr_player = PLAYER_O if curr_player == PLAYER_X else PLAYER_X

        for _ in path:
            self.undo_move()

        if winner:
            diff = self.calculate_difficulty(path, winner, start_player)
            return True, winner, math.ceil(len(path)/2), diff, path
        else:
            return False, None, 0, 0, path

def get_coord(prompt):
    while True:
        try:
            inp = input(prompt).strip().split()
            r, c = int(inp[0]), int(inp[1])
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE: return r, c
        except: pass
        print("Zadejte platné souřadnice ve formátu 'ŘÁDEK SLOUPEC' (0-14).")

def play_match_vs_ai(engine, start_player=PLAYER_O):
    print("NASTAVENÍ HRY PROTI POČÍTAČI")
    print("Zvolte si stranu:")
    print("1 - Kolečko (O) - jste na tahu jako 4. kámen v pořadí")
    print("2 - Křížek (X) - počítač zahraje 4. tah za Kolečko")
    print("3 - Nechat vybrat počítač (náhodně)")
    print("4 - Nechat vybrat počítač podle analýzy (počítač udělá rychlou analýzu a odhadne, která strana má lepší pozici)")
    
    choice = input("Volba (1-4, výchozí 1): ").strip()
    if choice == '4':
        score_o = engine.alpha_beta(0, 3, -math.inf, math.inf, True, PLAYER_O)
        score_x = engine.alpha_beta(0, 3, -math.inf, math.inf, True, PLAYER_X)
        
        if score_o >= score_x:
            ai_player = PLAYER_O
        else:
            ai_player = PLAYER_X
            
        human_player = PLAYER_O if ai_player == PLAYER_X else PLAYER_X
        print(f"Počítač vyhodnotil pozici a zvolil si hrát za: {ai_player}")
    elif choice == '2':
        human_player = PLAYER_X
    elif choice == '3':
        human_player = random.choice([PLAYER_X, PLAYER_O])
        print(f"\nPočítač vám přidělil stranu: {human_player}")
    else:
        human_player = PLAYER_O

    ai_player = PLAYER_O if human_player == PLAYER_X else PLAYER_X
    
    print("\nZvolte obtížnost počítače:")
    print("1 - Lehká (hloubka 4)")
    print("2 - Střední (hloubka 6)")
    print("3 - Těžká (hloubka 8)")
    diff_choice = input("Volba (1-3, výchozí 2): ").strip()

    if diff_choice == '1':
        t_depth = 4
    elif diff_choice == '3':
        t_depth = 8
    else:
        t_depth = 6

    curr_player = start_player
    print(f"\nHra začíná! Vy hrajete za '{human_player}', počítač za '{ai_player}'.")

    while True:
        engine.print_board()

        if curr_player == human_player:
            print(f"--> VAŠ TAH ({human_player}) [Můžete napsat 'z' pro vrácení tahu]")
            while True:
                user_input = input(f"Zadejte souřadnice (řádek sloupec) nebo 'z' zpět: ").strip()
                
                if user_input.lower() in ['z', 'undo', 'zpět']:
                    if engine.undo_last_full_turn():
                        print("\n[!] Poslední tahy byly vráceny. Jste opět na tahu.")
                        break
                    else:
                        print("\n[!] Nelze vrátit tah (žádná historie).")
                        continue
                
                try:
                    parts = user_input.split()
                    r, c = int(parts[0]), int(parts[1])
                    if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                        if engine.board[r][c] != EMPTY:
                            print("Tato pozice je již obsazená! Vyberte jiné políčko.")
                            continue
                        engine.make_move(r, c, human_player)
                        break
                except:
                    pass
                print("Zadejte platné souřadnice ve formátu 'ŘÁDEK SLOUPEC' (0-14) nebo 'z'.")
            
            if user_input.lower() in ['z', 'undo', 'zpět']:
                continue
        else:
            print(f"--> TAH POČÍTAČE ({ai_player}) - Přemýšlím...")
            move = engine.get_best_move(ai_player, thinking_depth=t_depth)
            if not move:
                print("Počítač nenašel žádný platný tah. Remíza!")
                break
            r, c = move
            print(f"Počítač zahrál na souřadnice: {r} {c}")
            engine.make_move(r, c, ai_player)

        if engine.check_five(curr_player):
            engine.print_board()
            if curr_player == human_player:
                print(f"*** GRATULUJEME! Vyhrál jste (hráč {human_player})! ***")
            else:
                print(f"*** POČÍTAČ VYHRÁL (hráč {ai_player})! Více štěstí příště. ***")
            break

        if all(engine.board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)):
            engine.print_board()
            print("*** Remíza! Deska je zcela zaplněna. ***")
            break

        curr_player = PLAYER_O if curr_player == PLAYER_X else PLAYER_X

if __name__ == "__main__":
    engine = InteractiveGomokuEngine()
    
    while True:
        print("PIŠKVORKY AI")
        
        print("Zadejte 3 úvodní kameny (SWAP 1):")
        rx1, cx1 = get_coord("1. Křížek (X): ")
        engine.make_move(rx1, cx1, PLAYER_X)
        rx2, cx2 = get_coord("2. Křížek (X): ")
        engine.make_move(rx2, cx2, PLAYER_X)
        ro1, co1 = get_coord("1. Kolečko (O): ")
        engine.make_move(ro1, co1, PLAYER_O)

        engine.print_board()

        print("Co si přejete po zadaném swapu udělat?")
        print("1 - Zahrát si PARTII PROTI POČÍTAČI z této pozice")
        print("2 - Spustit AUTOMATICKOU ANALÝZU (simulaci vývoje pomocí mého algoritmu, nemusí odpovídat optimální herní linii)")
        
        mode_choice = input("Volba (1-2, výchozí 1): ").strip()
        
        if mode_choice == '2':
            while True:
                try:
                    t_depth = input("\nHloubka přemýšlení na jeden tah (doporučeno 6): ").strip()
                    t_depth = int(t_depth) if t_depth else 6
                    
                    max_s = input("Maximální délka předpovídané sekvence (doporučeno 30): ").strip()
                    max_s = int(max_s) if max_s else 30
                except:
                    print("Chyba zadání. Používám výchozí hodnoty: hloubka 6, max 30 tahů.")
                    t_depth, max_s = 6, 30

                is_win, winner, moves, diff, path = engine.run_progressive_search(PLAYER_O, t_depth, max_s)

                print("\n---------------- VÝSLEDEK ANALÝZY ----------------")
                if is_win:
                    print(f"VÝHRA NALEZENA!")
                    print(f"Vítězný hráč: {winner}")
                    print(f"Tahů do výhry: {moves} (vlastních tahů vítěze)")
                    
                    diff_str = "Velmi intuitivní"
                    if diff > 3: diff_str = "Mírně náročné"
                    if diff > 10: diff_str = "Těžko odhalitelné"
                    
                    print(f"Náročnost: {diff} - {diff_str}")
                    print(f"Kompletní sekvence tahů: {path}")
                else:
                    print(f"Výhra v rámci {max_s} tahů nenalezena.")
                    print(f"Nejpravděpodobnější simulovaný vývoj hry: {path}")
                print("--------------------------------------------------")

                print("\nCo si přejete udělat níže?")
                print("1 - Změnit parametry hledání na stejné pozici")
                print("2 - Smazat desku a začít ZNOVU")
                print("3 - UKONČIT program")
                
                c = input("Volba (1-3): ").strip()
                if c == '1':
                    continue
                elif c == '3':
                    print("Program ukončen.")
                    exit()
                else:
                    engine.reset_board()
                    break
        else:
            play_match_vs_ai(engine, start_player=PLAYER_O)

            print("\nCo si přejete udělat po odehrané partii?")
            print("1 - Smazat desku a zadat NOVOU POZICI")
            print("2 - UKONČIT program")
            
            c = input("Volba (1-2): ").strip()
            if c == '2':
                print("Díky za hru! Program ukončen.")
                exit()
            else:
                engine.reset_board()
