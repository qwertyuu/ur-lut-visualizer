
function sketch1(p) {
    let img;
    let board_positions = `51,51	138,51	228,51
51,140	138,140	228,140
51,228	138,228	228,228
51,319	138,319	228,319
51,401	138,401	228,401
51,483	138,483	228,483
51,580	138,580	228,580
51,663	138,663	228,663`.split(/[\t\n]/);
    let pos_to_ignore = [12, 14, 15, 17];
    let final_board_positions = [];

    for (let i = 0; i < board_positions.length; i++) {
        if (pos_to_ignore.includes(i)) {
            continue;
        }
        final_board_positions.push(board_positions[i].split(","));
    }
    let player_pawn_positions = {
        "L": [
            final_board_positions[0],
            final_board_positions[1],
            final_board_positions[3],
            final_board_positions[4],
            final_board_positions[6],
            final_board_positions[7],
            final_board_positions[9],
            final_board_positions[10],
            final_board_positions[12],
            final_board_positions[13],
            final_board_positions[14],
            final_board_positions[15],
            final_board_positions[17],
            final_board_positions[18],
        ],
        "D": [
            final_board_positions[1],
            final_board_positions[2],
            final_board_positions[4],
            final_board_positions[5],
            final_board_positions[7],
            final_board_positions[8],
            final_board_positions[10],
            final_board_positions[11],
            final_board_positions[12],
            final_board_positions[13],
            final_board_positions[15],
            final_board_positions[16],
            final_board_positions[18],
            final_board_positions[19],
        ]
    }
    let pawns = [];
    let backgroundRatio = 1164 / 3050;
    let canvasSize = 720;
    let out_section_positions = [500, 500, canvasSize, canvasSize];

    // x, y, _path_index
    let index_to_2dpos = [
        [0, 0, 3],
        [1, 0, 4],
        [2, 0, 3],

        [0, 1, 2],
        [1, 1, 5],
        [2, 1, 2],

        [0, 2, 1],
        [1, 2, 6],
        [2, 2, 1],

        [0, 3, 0],
        [1, 3, 7],
        [2, 3, 0],

        [1, 4, 8],
        [1, 5, 9],

        [0, 6, 13],
        [1, 6, 10],
        [2, 6, 13],

        [0, 7, 12],
        [1, 7, 11],
        [2, 7, 12],
    ]

    p.setup = function () {
        p.createCanvas(canvasSize, canvasSize);
        p.rectMode(p.CORNERS);

        p.textSize(32);
        function createPawns(player_board_positions, player, column) {
            for (let i = 0; i < 7; i++) {
                const pawn = new Pawn(player_board_positions, p, player);
                pawn.position = p.createVector(p.width - 50 - column, 50 * i + 50);
                pawns.push(pawn);
            }
        }
        createPawns(player_pawn_positions["L"], "L", 0);
        createPawns(player_pawn_positions["D"], "D", 150);
        document.getElementById("submit").onclick = function () {
            const newState = {
                "D": {
                    left: 7,
                    board_positions: [],
                    score: 0,
                },
                "L": {
                    left: 7,
                    board_positions: [],
                    score: 0,
                },
                "currentPlayer": "L",
            };
            for (let i = 0; i < pawns.length; i++) {
                const pawn = pawns[i];
                if (
                    pawn.position.x >= out_section_positions[0]
                    && pawn.position.y >= out_section_positions[1]
                    && pawn.position.x <= out_section_positions[2]
                    && pawn.position.y <= out_section_positions[3]
                ) {
                    newState[pawn.player].score++;
                    newState[pawn.player].left--;
                }
                if (pawn.board_pos_hover != null) {
                    newState[pawn.player].board_positions.push(index_to_2dpos[final_board_positions.indexOf(pawn.board_pos_hover)]);
                    newState[pawn.player].left--;
                }
            }
            dash_clientside.set_props("store-events", { data: newState });
        }
    };
    p.draw = function () {
        p.background(32, 12, 133);
        p.image(img, 0, 0, canvasSize * backgroundRatio, canvasSize);

        p.fill(12);
        p.rect(out_section_positions[0], out_section_positions[1], out_section_positions[2], out_section_positions[3]);
        p.fill(255);
        p.text('OUT', out_section_positions[0], out_section_positions[1]);

        for (let i = 0; i < pawns.length; i++) {
            pawns[i].update();
        }
        for (let i = 0; i < pawns.length; i++) {
            pawns[i].draw();
        }
    };
    p.preload = function () {
        img = p.loadImage("/assets/image.png");
    };

    p.mousePressed = function () {
        const mouse = p.createVector(p.mouseX, p.mouseY);

        for (let i = 0; i < pawns.length; i++) {
            const vector = p5.Vector.sub(pawns[i].position, mouse);
            if (vector.magSq() <= 625) {
                pawns[i].stickToMouse();
                break;
            }
        }
    };

    p.mouseReleased = function () {
        for (let i = 0; i < pawns.length; i++) {
            pawns[i].releaseFromMouse();
        }
    };
}

function elementReady(selector) {
    return new Promise((resolve, reject) => {
        let el = document.querySelector(selector);
        if (el) {
            resolve(el);
            return
        }
        new MutationObserver((mutationRecords, observer) => {
            // Query for elements matching the specified selector
            Array.from(document.querySelectorAll(selector)).forEach((element) => {
                resolve(element);
                //Once we have resolved we don't need the observer anymore.
                observer.disconnect();
            });
        })
            .observe(document.documentElement, {
                childList: true,
                subtree: true
            });
    });
}

let listening = false;
setInterval(() => {
    if (!listening && !document.querySelector("#input-modal")) {
        elementReady('#input-modal').then(() => {
            new p5(sketch1, 'picker');
            listening = false;
        });
        listening = true;
    }
}, 500);