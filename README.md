# Projeto de Conclusão do Curso  
**Samsung Innovation Campus Brasil** com o **Senai Vila Mariana - Conectividade**  
[Mais informações sobre o programa](https://csr.samsung.com/pt/programViewSic.do) | [Sobre a unidade SENAI Conectividade](https://sp.senai.br/unidade/conectividade/)  

---

# EcoRotas 🌱  

O **EcoRotas** é uma solução inovadora para otimizar rotas logísticas com foco na sustentabilidade. A aplicação utiliza algoritmos avançados para:  
- **Minimizar o consumo de combustível**.  
- **Reduzir emissões de carbono**.  
- **Aumentar a eficiência operacional**.  

O projeto contribui diretamente para um futuro mais sustentável e eficiente no transporte logístico.  

---

## 🚀 Funcionalidades  

### 🔍 Planejamento de Rotas Otimizadas  
- Identifica as melhores rotas com base em:  
  - **Distância**.  
  - **Tempo estimado**.  
  - **Trajetos com velocidade média mais eficiente**.  

### 🌱 Análise de Impacto Ambiental  
- Calcula a **pegada de carbono** gerada em cada rota, promovendo escolhas mais ecológicas.  

### 🗺️ Integração com Mapas Interativos  
- Oferece uma visualização intuitiva das rotas diretamente em **mapas gerados com Folium**.  

---

## 🛠️ Tecnologias Utilizadas  

| Componente        | Ferramenta/Framework       |  
|-------------------|---------------------------|  
| **Frontend**      | HTML, CSS, JavaScript     |  
| **Backend**       | Flask (Python)            |  
| **Mapas**         | Folium, OSMnx             |  
| **Banco de Dados**| MySQL                     |  

---

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado em sua máquina:

- [Git](https://git-scm.com)
- [Python](https://www.python.org)
- [MySQL](https://www.python.org)
- [VS Code](https://code.visualstudio.com)

---

## 🧰 Como Instalar e Executar

1. Clone o repositório:
   ```bash
   git clone https://github.com/Mingarelli/EcoRotas.git
   cd EcoRotas
   cd Site
   ```
   
2. Instale as dependências no VS Code:

   O framework **OSMNx** é uma ferramenta essencial para realizar o geoprocessamento no projeto **EcoRotas**, permitindo o acesso a dados de mapas e a geração de rotas otimizadas.  
   ```bash
   pip install osmnx
   ```

   O **Flask** é o framework web utilizado no projeto **EcoRotas** para gerenciar o backend da aplicação. Ele fornece uma estrutura leve e flexível, permitindo a criação de APIs e o   processamento de dados necessários para a geração de rotas otimizadas e a análise do impacto ambiental.
   ```bash
   pip install flask
   ```
   
   O **MySQL Connector** é a biblioteca utilizada no projeto **EcoRotas** para conectar o backend, desenvolvido em Flask, ao banco de dados **MySQL**. Ele permite a execução de consultas, inserções e gerenciamento eficiente dos dados da aplicação.
   ```bash
   pip install mysql-connector-python
   ```

3. Executação no VS Code:

   No terminal executar os seguintes códigos:
   
   ```bash
   venv\Scripts\activate 
   ```
   
   Roda o código no local onde salvou:
   ```bash
   & C:/Users/xxxxx/xxxxx/xxxxxx/xxxxx/Site/venv/Scripts/python.exe c:/Users/xxxxx/xxxxxx/xxxxx/xxxxx/Site/meu_site.py
   ```

## 🌟 Exemplos de Uso

### 🚗 Planejamento de Rotas  
1. Faça login no sistema.  
2. Insira os **pontos de origem e destino**.  
3. Visualize:  
   - A **rota otimizada**.  
   - O **impacto ambiental calculado**.
  
---

## 📞 Contato  

Membros:

  **Camila Coelho**  
  - [LinkedIn](https://www.linkedin.com/in/camila-coelho-dias/)  
  - [GitHub](https://github.com/Camila-Coelho-Dias)  
  - **Email**: [camiladias4004@gmail.com](mailto:camiladias4004@gmail.com)

  **Eduardo Barreto**  
  - [LinkedIn](https://www.linkedin.com/in/eduardo-b-b165b9116/)  
  - [GitHub](https://github.com/VieiraEduardo)  
  - **Email**: [eduardo.bviera@gmail.com](mailto:eduardo.bviera@gmail.com)  

  **Guilherme Mingarelli**  
  - [LinkedIn](https://www.linkedin.com/in/guilherme-santiago-mingarelli-30b67395/)  
  - [GitHub](https://github.com/Mingarelli)  
  - **Email**: [guilhermemingarelli@gmail.com](mailto:guilhermemingarelli@gmail.com)

Orientador:

  **Tércio Ribeiro**  
  - [LinkedIn](https://www.linkedin.com/in/tercio-ribeiro/)  
  - [GitHub](https://github.com/tbribeiro05)  
  - **Email**: [terciobr05@hotmail.com](mailto:terciobr05@hotmail.com)

