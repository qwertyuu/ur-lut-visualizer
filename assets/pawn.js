class Pawn {
    constructor(final_board_positions, p5, player) {
        this.player = player;
        this.position = p5.createVector(0, 0);
        this.p5 = p5;
        this._stickToMouse = false;
        this.board_positions = final_board_positions;

        if (player == "D") {
            this.base_color = p5.color(39, 39, 39);
        } else {
            this.base_color = p5.color(255, 255, 255);
        }
        this.is_translucent = true;
        this.board_pos_hover = null;
    }

    stickToMouse() {
        this._stickToMouse = true;
    }

    releaseFromMouse() {
        this._stickToMouse = false;
    }

    update() {
        if (this._stickToMouse) {
            this.position = this.p5.createVector(
                Math.max(Math.min(this.p5.mouseX, this.p5.width), 0),
                Math.max(Math.min(this.p5.mouseY, this.p5.height), 0),
            );
            this.board_pos_hover = null;
            this.is_translucent = true;
            for (let i = 0; i < this.board_positions.length; i++) {
                let [x, y] = this.board_positions[i];
                const boardVec = this.p5.createVector(x, y);
                const vector = p5.Vector.sub(boardVec, this.position);
                if (vector.magSq() <= 625) {
                    this.is_translucent = false;
                    this.board_pos_hover = this.board_positions[i];
                    break;
                }
            }
        }
    }

    setBoardPos(board_pos) {
        if (!this.board_positions.includes(board_pos)) {
            throw new Error("Whoops, board pos is not in the available board positions for this player");
        }
        this.is_translucent = false;
        this.board_pos_hover = board_pos;
        this.position = this.p5.createVector(board_pos[0], board_pos[1]);
    }

    draw() {
        const draw_color = this.p5.color(this.base_color);
        draw_color.setAlpha(this.is_translucent ? 127 : 255);
        this.p5.fill(draw_color);
        this.p5.circle(this.position.x, this.position.y, 50);
    }
}