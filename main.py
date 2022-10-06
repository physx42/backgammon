# backgammon

from board import Board
from colour import Colour




if __name__ == '__main__':
    agent = Agent(0.1, 0.01, 0.7, 196)

    for episode in range(0, 100):
        print(f"--------- BEGIN EPISODE {episode} -----------")
        b = Board(debug_print=False, simple_board=True)
        b.choose_first_player()

        while True:
            b.record_initial_board_for_player()
            dice_rolls = b.roll_dice()
            b.print(f"Dice rolls: {dice_rolls}")
            move_tree, board_tree = b.get_possible_moves_from_dice(dice_rolls)
            b.print_move_tree(move_tree)
            b.simple_board_representation("Initial board:", header=True)
            possible_boards = board_tree.get_list_of_leaves(top=True)
            b.print(f"Number of possible moves: {len(possible_boards)}")
            b.print(f"{len(possible_boards)} possible boards")
            if len(board_tree.children) > 0:
                board_assessments = []
                for possible_board in possible_boards:
                    b.simple_board_representation("", possible_board, count=len(board_assessments))
                    board_features = b.calculate_board_features(possible_board)
                    board_assessments.append(agent.assess_features(board_features).numpy().item())
                action_index = agent.epsilon_greedy_action(board_assessments, print_outputs=b.print_boards)
                # Perform chosen action
                b.enact_provisional_move(possible_boards[action_index])

                # Train
                if b.current_player == Colour.Red:
                    last_features = b.last_red_features
                else:
                    last_features = b.last_white_features
                agent.train(last_features, b.calculate_board_features(b.board), reward=0)

            if b.game_over():
                break
            else:
                b.change_player()

        # Allow to learn from the game win
        if b.current_player == Colour.Red:
            last_features = b.last_red_features
        else:
            last_features = b.last_white_features
        agent.train(last_features, b.calculate_board_features(b.board), reward=1)

        print(f"Game over! Game won by {b.current_player}")



