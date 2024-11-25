-- Banco de Dados
CREATE DATABASE SistemaUsuariosGPS;
USE SistemaUsuariosGPS;

-- Tabela de Usuarios 
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    senha VARCHAR(100) NOT NULL
);

-- Endereços com ponto de partida e ponto de chegada
CREATE TABLE enderecos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    latitude_inicio DECIMAL(9, 6) NOT NULL,
    longitude_inicio DECIMAL(9, 6) NOT NULL,
    latitude_fim DECIMAL(9, 6) NOT NULL,
    longitude_fim DECIMAL(9, 6) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Criando Usuarios
INSERT INTO usuarios (email, senha)
VALUES ('admin@example.com', 'senha123');

-- Endereço com pontos de partida e chegada para o usuário
INSERT INTO enderecos (usuario_id, latitude_inicio, longitude_inicio, latitude_fim, longitude_fim)
VALUES (1, -23.550520, -46.633308, -22.906847, -43.172896);

-- Consultar todos os usuários
SELECT * FROM usuarios;

-- Consultar endereços e coordenadas de partida e chegada
SELECT e.id, u.email, e.latitude_inicio, e.longitude_inicio, e.latitude_fim, e.longitude_fim
FROM enderecos e
JOIN usuarios u ON e.usuario_id = u.id;

-- Atualizando o ponto de chegada do endereço
UPDATE enderecos
SET latitude_fim = -23.555773, longitude_fim = -46.639557
WHERE id = 1;

