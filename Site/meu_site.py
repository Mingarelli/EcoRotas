from flask import Flask, render_template, request, jsonify, session  # Importa as classes Flask, render_template, request e jsonify do módulo Flask para construir a aplicação web
import osmnx as ox  # Importa o osmnx, que facilita a extração e manipulação de dados de grafos urbanos e rotas
import folium  # Importa o folium, uma biblioteca para criar mapas interativos
import mysql.connector # Biblioteca para conectar com MySQL
from folium.plugins import MarkerCluster

# Inicializa a aplicação Flask
app = Flask(__name__)

app.secret_key = 'Mack3151@'

# Conecte ao banco de dados MySQL
db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "Mack3151@",
    database = "SistemaUsuariosGPS"
)

# Variável global para armazenar o grafo da cidade, que será utilizado para calcular as rotas
G = None

# Função de configuração para carregar o grafo da cidade usando osmnx
def configOsmnx():
    global G  # Usa a variável global G
    ox.config(use_cache=True, log_console=True)  # Configura o osmnx para utilizar cache, evitando carregar dados repetidamente, e exibir logs no console
    try:
        # Carrega o grafo da rede viária da cidade de São Paulo, configurado para o tipo 'drive', usado para simular rotas de carros
        G = ox.graph_from_place('São Paulo, São Paulo, Brazil', network_type='drive')
        print("Grafo carregado com sucesso!")  # Mensagem de sucesso ao carregar o grafo
    except Exception as e:
        # Exibe mensagem de erro caso o grafo não seja carregado corretamente
        print(f"Erro ao carregar o grafo: {e}")

# Rota inicial para renderizar a página e o mapa
@app.route("/")
def home():
    # Configurando o mapa inicial em São Paulo
    route_map = folium.Map(location=[-23.55052, -46.633308], control_scale=True, zoom_start=14)
    
    # Salvando o mapa como HTML para ser renderizado na página
    route_map.save("templates/mapa_sp.html")
    
    return render_template("app.html")  # Renderiza o HTML principal

# Rota que redireciona para a página de rotas, também sem o mapa carregado inicialmente
@app.route("/rotas")
def rotas():
    # Recupera o ID do usuário da sessão
    user_id = session.get('user_id')

    if user_id:
        cursor = db.cursor()
        cursor.execute("SELECT nome, sobrenome FROM usuarios WHERE id = %s", (user_id,))
        usuario = cursor.fetchone()

        if usuario:
            nome, sobrenome = usuario
            return render_template("paginarota.html", nome=nome, sobrenome=sobrenome)  # Renderiza o template com nome e sobrenome
        else:
            return "Usuário não encontrado", 404
    else:
        return "Usuário não está autenticado", 401

# Rota de login para validação
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s AND senha = %s", (username, password))
    user = cursor.fetchone()

    if user:
        # Armazena o ID do usuário na sessão
        session['user_id'] = user['id']
        return jsonify({"success": True})  # Login bem-sucedido
    else:
        return jsonify({"success": False})  # Falha no login

# Rota para buscar e calcular a rota entre dois pontos fornecidos pelo usuário
@app.route("/buscar_rota", methods=['POST'])
def buscar_rota():
    # Obtém as coordenadas dos pontos de partida e destino a partir do formulário enviado via POST
    ponto_partida = request.form.get('start')  # Recebe o ponto de partida inserido pelo usuário
    destino = request.form.get('end')  # Recebe o destino inserido pelo usuário
    
    try:
        # Converte os endereços fornecidos em coordenadas geográficas (latitude e longitude)
        partida_coords = ox.geocoder.geocode(ponto_partida)
        destino_coords = ox.geocoder.geocode(destino)

        # Calcula o ponto central entre partida e destino para ser o centro do mapa
        point = ((partida_coords[0] + destino_coords[0]) / 2,
                 (partida_coords[1] + destino_coords[1]) / 2)

        # Adiciona um novo nó ao grafo 'G' representando o ponto de partida com um ID único
        id_origem = max(G.nodes) + 1
        G.add_node(id_origem, y=partida_coords[0], x=partida_coords[1])

        # Adiciona um novo nó ao grafo 'G' representando o ponto de destino com outro ID único
        id_destino = max(G.nodes) + 1
        G.add_node(id_destino, y=destino_coords[0], x=destino_coords[1])

        # Encontra a aresta mais próxima do grafo 'G' para o ponto de partida
        orig_inicial, dist_inicial = ox.nearest_edges(G, partida_coords[1], partida_coords[0], return_dist=True)

        # Encontra a aresta mais próxima do grafo 'G' para o ponto de destino
        orig_final, dist_final = ox.nearest_edges(G, destino_coords[1], destino_coords[0], return_dist=True)

        # Conecta o ponto de destino aos nós próximos no grafo com base na distância calculada
        for i in range(len(orig_final)):
            if orig_final[i] != 0:
                id = orig_final[i]
                distancia = ox.distance.great_circle(
                    destino_coords[0],
                    destino_coords[1],
                    G.nodes()[id]['y'],
                    G.nodes()[id]['x']
                )
                G.add_edge(id_destino, id, length=distancia, highway="residential")
                G.add_edge(id, id_destino, length=distancia, highway="residential")

        # Conecta o ponto de origem aos nós próximos no grafo com base na distância calculada
        for i in range(len(orig_inicial)):
            if orig_inicial[i] != 0:
                id = orig_inicial[i]
                distancia = ox.distance.great_circle(
                    partida_coords[0],
                    partida_coords[1],
                    G.nodes()[id]['y'],
                    G.nodes()[id]['x']
                )
                G.add_edge(id_origem, id, length=distancia, highway="residential")
                G.add_edge(id, id_origem, length=distancia, highway="residential")

        # Calcula a rota mais curta no grafo entre o ponto de origem e o ponto de destino
        route1 = ox.routing.shortest_path(G, id_origem, id_destino, weight='length')

        # Definindo as velocidades médias (em km/h) para diferentes tipos de rodovias
        hwy_speeds = {
            "residential": 35,  # Velocidade média para ruas residenciais
            "secondary": 50,    # Velocidade média para ruas secundárias
            "tertiary": 60      # Velocidade média para ruas terciárias
        }

        # Adicionando as velocidades às arestas do grafo G usando as velocidades definidas acima
        #Essa função irá atribuir a cada aresta do grafo uma velocidade com base no tipo de rodovia
        ox.add_edge_speeds(G, hwy_speeds = hwy_speeds)

        # calculate travel time (seconds) for all edges
        ox.add_edge_travel_times(G)

        # Calculando a rota mais curta entre o id_origem e o id_destino
        # O parâmetro 'weight' é definido como 'travel_time', que considera o tempo de viagem ao invés da distância
        route2 = ox.routing.shortest_path(G, id_origem, id_destino, weight='travel_time')

        route3 = ox.routing.shortest_path(G, id_origem, id_destino, weight='speed_kph')

        # Converte o grafo 'G' para GeoDataFrames, obtendo apenas as arestas (edges)
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # Extrai a geometria das ruas associadas ao nó de origem e destino para uso no mapa
        rua_origem = list(edges['geometry'][orig_inicial[0]][orig_inicial[1]][orig_inicial[2]].coords)
        rua_destino = list(edges['geometry'][orig_final[0]][orig_final[1]][orig_final[2]].coords)

        # Inicializa o mapa com a localização central entre os pontos de origem e destino
        route_map = folium.Map(location=point, control_scale=True, zoom_start=14)

        # Adiciona marcadores no mapa para os pontos de partida e destino
        folium.Marker(location=[partida_coords[0], partida_coords[1]], icon=folium.Icon(color='blue', icon='user')).add_to(route_map)
        folium.Marker(location=[destino_coords[0], destino_coords[1]], icon=folium.Icon(color='green', icon='screenshot')).add_to(route_map)

        # Traça uma linha entre os pontos intermediários da rota
        linha = []
        for j in range(1, len(route1) - 2):
            temp = list(edges['geometry'][route1[j]][route1[j+1]][0].coords)
            for k in range(len(temp)):
                linha.append([temp[k][1], temp[k][0]])

        # Adiciona a linha de rota no mapa
        folium.PolyLine(
                        linha,
                        color='#003366',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Menor Distância.").add_to(route_map)
        folium.PolyLine(locations=linha, color='#3399ff', opacity=0.7, weight=4, tooltip="Trajeto de Menor Distância.").add_to(route_map)
        
        # Inicializa uma lista vazia chamada 'linha' que armazenará os pontos (coordenadas) da rota 2.
        linha = []

        # Loop que percorre os nós da rota 'route1', começando do segundo nó até o penúltimo.
        # 'range(1, len(route) - 2)' garante que o loop percorra todos os nós intermediários da rota 2.
        for j in range(1, len(route2) - 2):

            # Extrai a geometria (coordenadas) da aresta entre os nós consecutivos 'route2[j]' e 'route2[j+1]'.
            # A função 'edges['geometry']' acessa a geometria da aresta entre esses dois nós, onde '0' refere-se
            # ao índice da primeira (e provavelmente única) linha na geometria dessa aresta.
            # 'coords' extrai as coordenadas da linha e 'list()' converte essas coordenadas em uma lista.
            temp = list(edges['geometry'][route2[j]][route2[j+1]][0].coords)

            # Itera sobre todas as coordenadas (pontos) extraídas para a aresta atual (entre 'route2[j]' e 'route2[j+1]').
            for k in range(0, len(temp)):

                # Adiciona cada ponto à lista 'linha', trocando a ordem das coordenadas de (x, y) para (y, x),
                # pois o folium espera que as coordenadas estejam no formato [latitude, longitude].
                # 'temp[k][1]' é a latitude e 'temp[k][0]' é a longitude.
                linha.append([temp[k][1], temp[k][0]])

        # Desenha uma linha no mapa ('route_map') usando as coordenadas da lista 'linha'.
        # 'locations=linha' define os pontos da linha, e define a cor da linha (vermelho) e opacidade de 50%.
        folium.PolyLine(
                        linha,
                        color='#b20000',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Menor Tempo.").add_to(route_map)
        folium.PolyLine(locations=linha, color='#ff0000', opacity=0.7, weight=4, tooltip="Trajeto de Menor Tempo.").add_to(route_map)

        # Inicializa uma lista vazia chamada 'linha' que armazenará os pontos (coordenadas) da rota 2.
        linha = []

        # Loop que percorre os nós da rota 'route1', começando do segundo nó até o penúltimo.
        # 'range(1, len(route) - 2)' garante que o loop percorra todos os nós intermediários da rota 2.
        for j in range(1, len(route3) - 2):

            # Extrai a geometria (coordenadas) da aresta entre os nós consecutivos 'route2[j]' e 'route2[j+1]'.
            # A função 'edges['geometry']' acessa a geometria da aresta entre esses dois nós, onde '0' refere-se
            # ao índice da primeira (e provavelmente única) linha na geometria dessa aresta.
            # 'coords' extrai as coordenadas da linha e 'list()' converte essas coordenadas em uma lista.
            temp = list(edges['geometry'][route3[j]][route3[j+1]][0].coords)

            # Itera sobre todas as coordenadas (pontos) extraídas para a aresta atual (entre 'route2[j]' e 'route2[j+1]').
            for k in range(0, len(temp)):

                # Adiciona cada ponto à lista 'linha', trocando a ordem das coordenadas de (x, y) para (y, x),
                # pois o folium espera que as coordenadas estejam no formato [latitude, longitude].
                # 'temp[k][1]' é a latitude e 'temp[k][0]' é a longitude.
                linha.append([temp[k][1], temp[k][0]])

        # Desenha uma linha no mapa ('route_map') usando as coordenadas da lista 'linha'.
        # 'locations=linha' define os pontos da linha, e define a cor da linha (vermelho) e opacidade de 50%.
        folium.PolyLine(
                        linha,
                        color='#006400',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto com Melhor Velocidade.").add_to(route_map)
        folium.PolyLine(locations=linha, color='#00ff00', opacity=0.7, weight=4, tooltip="Trajeto com Melhor Velocidade.").add_to(route_map)


        # Traça a linha final que conecta os pontos ao destino
        linha_destino = []
        if rua_destino[0][0] == G.nodes[route1[-2]]['x'] and rua_destino[0][1] == G.nodes[route1[-2]]['y']:
            for i in range(len(rua_destino)):
                ponto_origem = ox.distance.great_circle(destino_coords[1], destino_coords[0], rua_destino[i][0], rua_destino[i][1])
                if i > 0 and ponto_origem > ponto_antecessor or ponto_origem == 0:
                    linha_destino.append([destino_coords[0], destino_coords[1]])
                    break
                linha_destino.append([rua_destino[i][1], rua_destino[i][0]])
                ponto_antecessor = ponto_origem
        else:
            linha_destino.append([destino_coords[0], destino_coords[1]])
            linha_destino.append([rua_destino[-1][1], rua_destino[-1][0]])

        if linha_destino:
            folium.PolyLine(
                        linha_destino,
                        color='#003366',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Menor Distância.").add_to(route_map)
            folium.PolyLine(locations=linha_destino, color='#3399ff', opacity=0.7, weight=4, tooltip="Trajeto de Menor Distância.").add_to(route_map)

        linha_origem = []
        if rua_origem[0][0] == G.nodes[route1[1]]['x'] and rua_origem[0][1] == G.nodes[route1[1]]['y']:
            for i in range(len(rua_origem)):
                ponto_origem = ox.distance.great_circle(partida_coords[1], partida_coords[0], rua_origem[i][0], rua_origem[i][1])
                if i > 0 and ponto_origem > ponto_antecessor or ponto_origem == 0:
                    linha_origem.append([partida_coords[0], partida_coords[1]])
                    break
                linha_origem.append([rua_origem[i][1], rua_origem[i][0]])
                ponto_antecessor = ponto_origem
        else:
            linha_origem.append([partida_coords[0], partida_coords[1]])
            linha_origem.append([rua_origem[-1][1], rua_origem[-1][0]])

        if linha_origem:
            folium.PolyLine(
                        linha_origem,
                        color='#003366',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Menor Distância.").add_to(route_map)
            folium.PolyLine(locations=linha_origem, color='#3399ff', opacity=0.7,weight=4, tooltip="Trajeto de Menor Distância.").add_to(route_map)

        # A variável 'coordenadas_nodo' obtém as coordenadas (x, y) do penúltimo nó da rota ('route2[-2]') do grafo 'G'.
        coordenadas_nodo = G.nodes[route2[-2]]

        # Inicializa uma lista 'linha_destino' para armazenar os pontos da linha de destino que será desenhada.
        linha_destino = []

        # Verifica se o primeiro ponto de 'rua_destino' coincide com as coordenadas do nó atual.
        if rua_destino[0][0] == coordenadas_nodo['x'] and rua_destino[0][1] == coordenadas_nodo['y']:
            # Percorre os pontos em 'rua_destino' para calcular a distância entre os pontos da rota e as coordenadas finais.
            for i in range(0, len(rua_destino)):
                # Calcula a distância entre 'coordenada_final' e os pontos em 'rua_destino' usando a fórmula do círculo máximo.
                ponto_origem = ox.distance.great_circle(destino_coords[1], destino_coords[0], rua_destino[i][0], rua_destino[i][1])

                # Verifica se a distância atual é maior que a distância do ponto anterior ou se a distância é zero.
                if i > 0 and ponto_origem > ponto_antecessor or ponto_origem == 0:
                    # Se a condição for verdadeira, adiciona 'coordenada_final' à linha de destino e encerra o loop.
                    linha_destino.append([destino_coords[0], destino_coords[1]])
                    break

                # Adiciona o ponto atual de 'rua_destino' à lista 'linha_destino'.
                linha_destino.append([rua_destino[i][1], rua_destino[i][0]])

                # Atualiza a variável 'ponto_antecessor' com a distância atual para a próxima iteração.
                ponto_antecessor = ponto_origem
        else:
            # Caso as coordenadas não coincidam, adiciona 'coordenada_final' e o último ponto de 'rua_destino' à linha de destino.
            linha_destino.append([destino_coords[0], destino_coords[1]])
            linha_destino.append([rua_destino[-1][1], rua_destino[-1][0]])

        # Se a lista 'linha_destino' não estiver vazia, desenha uma linha vermelha no mapa ('route_map') com os pontos da lista.
        if len(linha_destino) > 0:
            folium.PolyLine(
                        linha_destino,
                        color='#b20000',     
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Menor Tempo.").add_to(route_map)
            folium.PolyLine(locations=linha_destino, color='#ff0000', opacity=0.7, weight=4, tooltip="Trajeto de Menor Tempo.").add_to(route_map)


        # A variável 'coordenadas_nodo' agora obtém as coordenadas do segundo nó da rota ('route[1]').
        coordenadas_nodo = G.nodes[route2[1]]

        # Inicializa uma lista 'linha_origem' para armazenar os pontos da linha de origem que será desenhada.
        linha_origem = []

        # Verifica se o primeiro ponto de 'rua_origem' coincide com as coordenadas do nó atual.
        if rua_origem[0][0] == coordenadas_nodo['x'] and rua_origem[0][1] == coordenadas_nodo['y']:
            # Percorre os pontos em 'rua_origem' para calcular a distância entre os pontos da rota e as coordenadas iniciais.
            for i in range(0, len(rua_origem)):
                # Calcula a distância entre 'coordenada_inicial' e os pontos em 'rua_origem' usando a fórmula do círculo máximo.
                ponto_origem = ox.distance.great_circle(partida_coords[1], partida_coords[0], rua_origem[i][0], rua_origem[i][1])

                # Verifica se a distância atual é maior que a distância do ponto anterior ou se a distância é zero.
                if i > 0 and ponto_origem > ponto_antecessor or ponto_origem == 0:
                    # Se a condição for verdadeira, adiciona 'coordenada_inicial' à linha de origem e encerra o loop.
                    linha_origem.append([partida_coords[0], partida_coords[1]])
                    break

                # Adiciona o ponto atual de 'rua_origem' à lista 'linha_origem'.
                linha_origem.append([rua_origem[i][1], rua_origem[i][0]])

                # Atualiza a variável 'ponto_antecessor' com a distância atual para a próxima iteração.
                ponto_antecessor = ponto_origem

        else:
            # Caso as coordenadas não coincidam, adiciona 'coordenada_inicial' e o último ponto de 'rua_origem' à linha de origem.
            linha_origem.append([partida_coords[0], partida_coords[1]])
            linha_origem.append([rua_origem[-1][1], rua_origem[-1][0]])

        # Se a lista 'linha_origem' não estiver vazia, desenha uma linha vermelha no mapa ('route_map') com os pontos da lista.
        if len(linha_origem) > 0:
            folium.PolyLine(
                        linha_origem,
                        color='#b20000',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Menor Tempo.").add_to(route_map)
            folium.PolyLine(locations=linha_origem, color="#ff0000", opacity=0.7, weight=4, tooltip="Trajeto de Menor Tempo.").add_to(route_map)
        
        # A variável 'coordenadas_nodo' obtém as coordenadas (x, y) do penúltimo nó da rota ('route2[-2]') do grafo 'G'.
        coordenadas_nodo = G.nodes[route3[-2]]

        # Inicializa uma lista 'linha_destino' para armazenar os pontos da linha de destino que será desenhada.
        linha_destino = []

        # Verifica se o primeiro ponto de 'rua_destino' coincide com as coordenadas do nó atual.
        if rua_destino[0][0] == coordenadas_nodo['x'] and rua_destino[0][1] == coordenadas_nodo['y']:
            # Percorre os pontos em 'rua_destino' para calcular a distância entre os pontos da rota e as coordenadas finais.
            for i in range(0, len(rua_destino)):
                # Calcula a distância entre 'coordenada_final' e os pontos em 'rua_destino' usando a fórmula do círculo máximo.
                ponto_origem = ox.distance.great_circle(destino_coords[1], destino_coords[0], rua_destino[i][0], rua_destino[i][1])

                # Verifica se a distância atual é maior que a distância do ponto anterior ou se a distância é zero.
                if i > 0 and ponto_origem > ponto_antecessor or ponto_origem == 0:
                    # Se a condição for verdadeira, adiciona 'coordenada_final' à linha de destino e encerra o loop.
                    linha_destino.append([destino_coords[0], destino_coords[1]])
                    break

                # Adiciona o ponto atual de 'rua_destino' à lista 'linha_destino'.
                linha_destino.append([rua_destino[i][1], rua_destino[i][0]])

                # Atualiza a variável 'ponto_antecessor' com a distância atual para a próxima iteração.
                ponto_antecessor = ponto_origem
        else:
            # Caso as coordenadas não coincidam, adiciona 'coordenada_final' e o último ponto de 'rua_destino' à linha de destino.
            linha_destino.append([destino_coords[0], destino_coords[1]])
            linha_destino.append([rua_destino[-1][1], rua_destino[-1][0]])

        # Se a lista 'linha_destino' não estiver vazia, desenha uma linha vermelha no mapa ('route_map') com os pontos da lista.
        if len(linha_destino) > 0:
            folium.PolyLine(
                        linha_destino,
                        color='#006400',     
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Melhor Velocidade.").add_to(route_map)
            folium.PolyLine(locations=linha_destino, color='#00ff00', opacity=0.7, weight=4, tooltip="Trajeto de Melhor Velocidade").add_to(route_map)


        # A variável 'coordenadas_nodo' agora obtém as coordenadas do segundo nó da rota ('route[1]').
        coordenadas_nodo = G.nodes[route3[1]]

        # Inicializa uma lista 'linha_origem' para armazenar os pontos da linha de origem que será desenhada.
        linha_origem = []

        # Verifica se o primeiro ponto de 'rua_origem' coincide com as coordenadas do nó atual.
        if rua_origem[0][0] == coordenadas_nodo['x'] and rua_origem[0][1] == coordenadas_nodo['y']:
            # Percorre os pontos em 'rua_origem' para calcular a distância entre os pontos da rota e as coordenadas iniciais.
            for i in range(0, len(rua_origem)):
                # Calcula a distância entre 'coordenada_inicial' e os pontos em 'rua_origem' usando a fórmula do círculo máximo.
                ponto_origem = ox.distance.great_circle(partida_coords[1], partida_coords[0], rua_origem[i][0], rua_origem[i][1])

                # Verifica se a distância atual é maior que a distância do ponto anterior ou se a distância é zero.
                if i > 0 and ponto_origem > ponto_antecessor or ponto_origem == 0:
                    # Se a condição for verdadeira, adiciona 'coordenada_inicial' à linha de origem e encerra o loop.
                    linha_origem.append([partida_coords[0], partida_coords[1]])
                    break

                # Adiciona o ponto atual de 'rua_origem' à lista 'linha_origem'.
                linha_origem.append([rua_origem[i][1], rua_origem[i][0]])

                # Atualiza a variável 'ponto_antecessor' com a distância atual para a próxima iteração.
                ponto_antecessor = ponto_origem

        else:
            # Caso as coordenadas não coincidam, adiciona 'coordenada_inicial' e o último ponto de 'rua_origem' à linha de origem.
            linha_origem.append([partida_coords[0], partida_coords[1]])
            linha_origem.append([rua_origem[-1][1], rua_origem[-1][0]])

        # Se a lista 'linha_origem' não estiver vazia, desenha uma linha vermelha no mapa ('route_map') com os pontos da lista.
        if len(linha_origem) > 0:
            folium.PolyLine(
                        linha_origem,
                        color='#006400',     # Borda preta
                        weight=8,           # Espessura da borda
                        tooltip="Trajeto de Melhor Velocidade.").add_to(route_map)
            folium.PolyLine(locations=linha_origem, color="#00ff00", opacity=0.7, weight=4, tooltip="Trajeto de Melhor Velocidade.").add_to(route_map)
        
        # compare the two routes
        route1_length = round(int(sum(ox.routing.route_to_gdf(G, route1, weight="length")["length"]))/1000,2)
        route2_length = round(int(sum(ox.routing.route_to_gdf(G, route2, weight="travel_time")["length"]))/1000,2)
        route3_length = round(int(sum(ox.routing.route_to_gdf(G, route3, weight="speed_kph")["length"]))/1000,2)

        '''
        Exemplo: Fiat Ducato 2.3 Multijet (Diesel)
        Para o Fiat Ducato 2.3 Multijet:

        Consumo médio de combustível: em torno de 10 a 12 km/l.
        Emissão de CO₂: aproximadamente 0,24 kg de CO₂ por km (considerando uma média de consumo e emissão para diesel).
        '''

        route1_co2 = round(route1_length * 0.24,2)
        route2_co2 = round(route2_length * 0.24,2)
        route3_co2 = round(route3_length * 0.24,2)

        route1_time = int(sum(ox.routing.route_to_gdf(G, route1, weight="length")["travel_time"]))
        route2_time = int(sum(ox.routing.route_to_gdf(G, route2, weight="travel_time")["travel_time"]))
        route3_time = int(sum(ox.routing.route_to_gdf(G, route3, weight="speed_kph")["travel_time"]))

        route1_time_mm = int(route1_time/60)
        route2_time_mm = int(route2_time/60)
        route3_time_mm = int(route3_time/60)

        route1_time = route1_time - (route1_time_mm * 60)
        route2_time = route2_time - (route2_time_mm * 60)
        route3_time = route3_time - (route3_time_mm * 60)

        route1_speed = round(int(sum(ox.routing.route_to_gdf(G, route1, weight="length")["speed_kph"]))/len(route1),1)
        route2_speed = round(int(sum(ox.routing.route_to_gdf(G, route2, weight="travel_time")["speed_kph"]))/len(route2),1)
        route3_speed = round(int(sum(ox.routing.route_to_gdf(G, route3, weight="speed_kph")["speed_kph"]))/len(route3),1)

        print("Trajeto de Menor Distância:", route1_length, "metros com o tempo de", route1_time_mm, ":", route1_time, "mm:ss e a emissão de CO2:", route1_co2, "kg de CO2")
        print("Trajeto de Menor Tempo:", route2_length, "metros com o tempo de", route2_time_mm, ":", route2_time, "mm:ss e a emissão de CO2:", route2_co2, "kg de CO2")
        print("Trajeto de Melhor Velocidade:", route3_length, "metros com o tempo de", route3_time_mm, ":", route3_time, "mm:ss e a emissão de CO2:", route3_co2, "kg de CO2")

         # Exemplo de dados das rotas (substitua com os valores reais)
        dados_rota = {
            "map_html": route_map._repr_html_(),
            "tempo_rota1": (str(route1_time_mm) + ":" + str(route1_time) + " min"),
            "distancia_rota1": (str(route1_length) + "km"),
            "velocidade_media_rota1": (str(route1_speed) + "km/h"),
            "emissao_co2_rota1": (str(route1_co2) + "kg"),
        
            "tempo_rota2": (str(route2_time_mm) + ":" + str(route2_time) + " min"),
            "distancia_rota2": (str(route2_length) + "km"),
            "velocidade_media_rota2": (str(route2_speed) + "km/h"),
            "emissao_co2_rota2": (str(route2_co2) + "kg"),
        
            "tempo_rota3": (str(route3_time_mm) + ":" + str(route3_time) + " min"),
            "distancia_rota3": (str(route3_length) + "km"),
            "velocidade_media_rota3": (str(route3_speed) + "km/h"),
            "emissao_co2_rota3": (str(route3_co2) + "kg")
        }

        # Retornando os dados como JSON
        return jsonify(dados_rota)
    
    except Exception as e:
        # Exibe mensagem de erro se ocorrer algum problema durante o cálculo da rota
        print(f"Erro ao calcular a rota: {e}")
        return jsonify({"error": "Não foi possível calcular a rota. Verifique os endereços e tente novamente."})

# Inicializa o servidor Flask e carrega o grafo ao iniciar
if __name__ == "__main__":
    configOsmnx()  # Chama a função para carregar o grafo
    app.run(debug=False)  # Executa o servidor Flask
