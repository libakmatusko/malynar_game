# malynar_game
Budu tu dva priečinky, jeden na server, ktorý bude bežať hru a jeden na aplikáciu/program, ktorý bude bežať každý hráč.

Popis buildings.json:
dictionary budov{
    nazov:{
        "requrement":string - potreby atribut policka vedla
        "generating":bool - ci je generujuca budova
        "cost":[
            {
                item:pocet
            }
        ] list - ku kazdemu levlu ma jeden dict
        "ticks per item": list - ku kazdemu levlu ma jeden int
        "input": [
            item:pocet
        ] list - ku kazdemu levlu ma jeden dict
        "output": [
            item:pocet
        ] list - ku kazdemu levlu ma jeden dict
        "design": {
            "shape": "triangle",
            "color": "purple"
        } ako sa orientovat vo farbach dopisat...
        "points" list z int k levlom
    }
}