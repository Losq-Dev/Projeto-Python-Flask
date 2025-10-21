from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
from decimal import Decimal
from dotenv import load_dotenv
import os
from sqlalchemy import func, or_, and_
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados MySQL
# IMPORTANTE: Ajuste as credenciais para o seu banco
# Carrega as credenciais do arquivo .env

DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'projeto')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =======================
# MODELOS (Tabelas)
# =======================

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nome_categoria = db.Column(db.String(20))
    
    def to_dict(self):
        return {
            'id_categoria': self.id_categoria,
            'nome_categoria': self.nome_categoria
        }

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    cnpj = db.Column(db.BigInteger, primary_key=True)
    nome_empresa = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'))
    
    categoria_obj = db.relationship('Categoria', backref='fornecedores')
    
    def to_dict(self):
        return {
            'cnpj': self.cnpj,
            'nome_empresa': self.nome_empresa,
            'categoria': self.categoria,
            'categoria_nome': self.categoria_obj.nome_categoria if self.categoria_obj else None
        }

class Cliente(db.Model):
    __tablename__ = 'clientes'
    cpf = db.Column(db.BigInteger, primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20)) 
    
    def to_dict(self):
        return {
            'cpf': self.cpf,
            'nome_cliente': self.nome_cliente,
            'telefone': self.telefone
        }

class Doca(db.Model):
    __tablename__ = 'docas'
    id_doca = db.Column(db.Integer, primary_key=True)
    
    def to_dict(self):
        return {'id_doca': self.id_doca}

class Produto(db.Model):
    __tablename__ = 'produtos'
    id_produto = db.Column(db.Integer, primary_key=True)
    nome_produto = db.Column(db.String(100), nullable=False)
    validade = db.Column(db.Date, nullable=False)
    lote = db.Column(db.BigInteger, nullable=False)
    categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=False)
    fornecedor = db.Column(db.BigInteger, db.ForeignKey('fornecedores.cnpj'), nullable=False)
    doca = db.Column(db.Integer, db.ForeignKey('docas.id_doca'))
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    
    categoria_obj = db.relationship('Categoria')
    fornecedor_obj = db.relationship('Fornecedor')
    doca_obj = db.relationship('Doca', foreign_keys='Produto.doca', backref='produtos_doca')
    
    def to_dict(self):
        return {
            'id_produto': self.id_produto,
            'nome_produto': self.nome_produto,
            'validade': self.validade.isoformat() if self.validade else None,
            'lote': self.lote,
            'categoria': self.categoria,
            'fornecedor': self.fornecedor,
            'doca': self.doca,
            'valor': float(self.valor),
            'quantidade': self.quantidade
        }

class Venda(db.Model):
    __tablename__ = 'vendas'
    
    id_venda = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pedido = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    produto = db.Column(db.Integer, db.ForeignKey('produtos.id_produto'), nullable=False)
    cliente_cpf = db.Column(db.BigInteger, db.ForeignKey('clientes.cpf'))
    data_venda = db.Column(db.Date, nullable=False)
    hora_venda = db.Column(db.Time, nullable=False)
    forma_pagamento = db.Column(db.String(20), nullable=False)

    produto_obj = db.relationship('Produto', backref='vendas')
    cliente_obj = db.relationship('Cliente', backref='vendas')

    def to_dict(self):
        return {
            'id_venda': self.id_venda,
            'id_pedido': self.id_pedido,
            'valor': float(self.valor),
            'quantidade': self.quantidade,
            'produto': self.produto,
            'produto_nome': self.produto_obj.nome_produto if self.produto_obj else None,
            'cliente_cpf': self.cliente_cpf,
            'data_venda': self.data_venda.isoformat() if self.data_venda else None,
            'hora_venda': self.hora_venda.isoformat() if self.hora_venda else None,
            'forma_pagamento': self.forma_pagamento
        }

class Login(db.Model):
    __tablename__ = 'login'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(50), nullable=False)

# =======================
# ROTA - LOGIN
# =======================

@app.route('/login', methods=['POST'])
def fazer_login():
    dados = request.get_json()
    usuario_form = dados.get('usuario')
    senha_form = dados.get('senha')

    if not usuario_form or not senha_form:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário e senha são obrigatórios'}), 400

    usuario_db = Login.query.filter_by(usuario=usuario_form).first()

    if usuario_db and usuario_db.senha == senha_form:
        return jsonify({'status': 'sucesso', 'mensagem': 'Login bem-sucedido!'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário ou senha inválidos'}), 401

# =======================
# ROTAS - CATEGORIAS
# =======================

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    categorias = Categoria.query.all()
    return jsonify([c.to_dict() for c in categorias])

@app.route('/categorias', methods=['POST'])
def criar_categoria():
    dados = request.get_json()
    if not dados.get('id_categoria') or not dados.get('nome_categoria'):
        return jsonify({'erro': 'id_categoria e nome_categoria são obrigatórios'}), 400
    
    nova_categoria = Categoria(
        id_categoria=dados['id_categoria'],
        nome_categoria=dados['nome_categoria']
    )
    db.session.add(nova_categoria)
    db.session.commit()
    return jsonify(nova_categoria.to_dict()), 201
    
# ROTA ADICIONADA (para página de categorias)
@app.route('/categorias/produtos', methods=['GET'])
def listar_categorias_com_produtos():
    termo_pesquisa = request.args.get('q', '').lower()
    
    query = Categoria.query
    
    if termo_pesquisa:
        query = query.filter(
            or_(
                Categoria.nome_categoria.like(f'%{termo_pesquisa}%'),
                func.cast(Categoria.id_categoria, db.String).like(f'%{termo_pesquisa}%')
            )
        )
        
    categorias = query.all()
    resultado = []
    
    for c in categorias:
        categoria_dict = c.to_dict()
        produtos = Produto.query.filter_by(categoria=c.id_categoria).all()
        categoria_dict['produtos'] = [p.to_dict() for p in produtos]
        resultado.append(categoria_dict)
        
    return jsonify(resultado)

# =======================
# ROTAS - CLIENTES
# =======================

@app.route('/clientes', methods=['GET'])
def listar_clientes():
    clientes = Cliente.query.all()
    return jsonify([c.to_dict() for c in clientes])

# ROTA ADICIONADA (para pesquisa)
@app.route('/clientes/search', methods=['GET'])
def buscar_clientes():
    termo_pesquisa = request.args.get('q', '').lower()
    
    query = Cliente.query.filter(
        or_(
            Cliente.nome_cliente.like(f'%{termo_pesquisa}%'),
            func.cast(Cliente.cpf, db.String).like(f'%{termo_pesquisa}%')
        )
    )
    
    clientes = query.all()
    return jsonify([c.to_dict() for c in clientes])

@app.route('/clientes', methods=['POST'])
def criar_cliente():
    dados = request.get_json()
    if not dados.get('cpf') or not dados.get('nome_cliente'):
        return jsonify({'erro': 'cpf e nome_cliente são obrigatórios'}), 400
    
    novo_cliente = Cliente(
        cpf=dados['cpf'],
        nome_cliente=dados['nome_cliente'],
        telefone=dados.get('telefone') # CAMPO ADICIONADO
    )
    db.session.add(novo_cliente)
    db.session.commit()
    return jsonify(novo_cliente.to_dict()), 201

@app.route('/clientes/<int:cpf>', methods=['PUT'])
def atualizar_cliente(cpf):
    cliente = Cliente.query.get(cpf)
    if not cliente:
        return jsonify({'erro': 'Cliente não encontrado'}), 404
    
    dados = request.get_json()
    if dados.get('nome_cliente'):
        cliente.nome_cliente = dados['nome_cliente']
    if 'telefone' in dados: # CAMPO ADICIONADO
        cliente.telefone = dados['telefone']
    
    db.session.commit()
    return jsonify(cliente.to_dict())


# =======================
# ROTAS - DOCAS
# =======================

@app.route('/docas', methods=['GET'])
def listar_docas():
    docas = Doca.query.all()
    return jsonify([d.to_dict() for d in docas])
    
# ROTA ADICIONADA (para página de docas)
@app.route('/docas/produtos', methods=['GET'])
def listar_docas_com_produtos():
    termo_pesquisa = request.args.get('q', '').lower()

    # Base query
    query = db.session.query(Doca, Produto).outerjoin(Produto, Doca.id_doca == Produto.doca)

    if termo_pesquisa:
        query = query.filter(
            or_(
                func.cast(Doca.id_doca, db.String).like(f'%{termo_pesquisa}%'),
                Produto.nome_produto.like(f'%{termo_pesquisa}%'),
                func.cast(Produto.id_produto, db.String).like(f'%{termo_pesquisa}%')
            )
        )
        
    query = query.order_by(Doca.id_doca)
    
    resultados = query.all()
    
    # Estruturar os dados
    lista_docas = []
    for doca, produto in resultados:
        item = {
            'doca': doca.id_doca,
            'id_produto': produto.id_produto if produto else None,
            'nome_produto': produto.nome_produto if produto else "--- VAZIA ---"
        }
        lista_docas.append(item)
        
    return jsonify(lista_docas)


@app.route('/docas', methods=['POST'])
def criar_doca():
    dados = request.get_json()
    if not dados.get('id_doca'):
        return jsonify({'erro': 'id_doca é obrigatório'}), 400
    
    nova_doca = Doca(
        id_doca=dados['id_doca']
        # 'produto' foi removido
    )
    db.session.add(nova_doca)
    db.session.commit()
    return jsonify(nova_doca.to_dict()), 201

# =======================
# ROTAS - PRODUTOS
# =======================

@app.route('/produtos', methods=['GET'])
def listar_produtos():
    produtos = Produto.query.all()
    return jsonify([p.to_dict() for p in produtos])
    
# ROTA ADICIONADA (para pesquisa)
@app.route('/produtos/search', methods=['GET'])
def buscar_produtos():
    termo_pesquisa = request.args.get('q', '').lower()
    
    query = Produto.query.filter(
        or_(
            Produto.nome_produto.like(f'%{termo_pesquisa}%'),
            func.cast(Produto.id_produto, db.String).like(f'%{termo_pesquisa}%')
        )
    )
    
    produtos = query.all()
    return jsonify([p.to_dict() for p in produtos])


@app.route('/produtos/<int:id>', methods=['GET'])
def buscar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    return jsonify(produto.to_dict())

@app.route('/produtos', methods=['POST'])
def criar_produto():
    dados = request.get_json()
    campos_obrigatorios = ['id_produto', 'nome_produto', 'validade', 'lote', 'categoria', 'fornecedor', 'valor', 'quantidade']
    
    for campo in campos_obrigatorios:
        if campo not in dados:
            return jsonify({'erro': f'{campo} é obrigatório'}), 400
    
    novo_produto = Produto(
        id_produto=dados['id_produto'],
        nome_produto=dados['nome_produto'],
        validade=datetime.strptime(dados['validade'], '%Y-%m-%d').date(),
        lote=dados['lote'],
        categoria=dados['categoria'],
        fornecedor=dados['fornecedor'],
        doca=dados.get('doca'),
        valor=dados['valor'],
        quantidade=dados['quantidade'] # CAMPO ADICIONADO
    )
    db.session.add(novo_produto)
    db.session.commit()
    return jsonify(novo_produto.to_dict()), 201

@app.route('/produtos/<int:id>', methods=['PUT'])
def atualizar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    
    dados = request.get_json()
    if dados.get('nome_produto'):
        produto.nome_produto = dados['nome_produto']
    if dados.get('validade'):
        produto.validade = datetime.strptime(dados['validade'], '%Y-%m-%d').date()
    if dados.get('lote'):
        produto.lote = dados['lote']
    if dados.get('categoria'):
        produto.categoria = dados['categoria']
    if dados.get('fornecedor'):
        produto.fornecedor = dados['fornecedor']
    if 'doca' in dados:
        produto.doca = dados['doca']
    if dados.get('valor'):
        produto.valor = dados['valor']
    if 'quantidade' in dados: # CAMPO ADICIONADO
        produto.quantidade = dados['quantidade']
    
    db.session.commit()
    return jsonify(produto.to_dict())

# =======================
# ROTAS - VENDAS (MODIFICADAS)
# =======================

# Esta rota agora lista todas as vendas (itens de venda)
@app.route('/vendas', methods=['GET'])
def listar_vendas():
    vendas = Venda.query.all()
    return jsonify([v.to_dict() for v in vendas])

# ROTA ADICIONADA (CRÍTICA PARA O FRONTEND)
@app.route('/vendas/finalizar', methods=['POST'])
def finalizar_venda():
    dados = request.get_json()
    
    # Dados esperados: { 'cliente_cpf': '...', 'forma_pagamento': '...', 'produtos': [ ... ] }
    if not dados.get('produtos') or not dados.get('forma_pagamento'):
        return jsonify({'erro': 'Lista de produtos e forma de pagamento são obrigatórios'}), 400
        
    try:
        produtos_carrinho = dados['produtos']
        forma_pagamento = dados['forma_pagamento']
        cliente_cpf = dados.get('cliente_cpf')
        
        # Pega o próximo 'id_pedido'. 
        # Em um sistema real, isso seria uma tabela 'pedidos', 
        # mas vamos usar o MAX(id_pedido) + 1 para simplificar.
        ultimo_pedido_id = db.session.query(func.max(Venda.id_pedido)).scalar() or 0
        novo_pedido_id = ultimo_pedido_id + 1
        
        agora = datetime.now()
        data_atual = agora.date()
        hora_atual = agora.time()

        novas_vendas_db = []
        
        for item in produtos_carrinho:
            id_produto = item['id_produto']
            qtd_vendida = item['quantidade']
            
            # 1. Verifica e atualiza o estoque
            produto_db = Produto.query.get(id_produto)
            if not produto_db:
                raise Exception(f"Produto ID {id_produto} não encontrado")
            
            if produto_db.quantidade < qtd_vendida:
                raise Exception(f"Estoque insuficiente para {produto_db.nome_produto}")
                
            produto_db.quantidade = produto_db.quantidade - qtd_vendida
            
            # 2. Cria o item de venda
            nova_venda = Venda(
                id_pedido=novo_pedido_id,
                valor=(Decimal(item['valor']) * qtd_vendida),
                quantidade=qtd_vendida,
                produto=id_produto,
                cliente_cpf=cliente_cpf if cliente_cpf else None,
                data_venda=data_atual,
                hora_venda=hora_atual,
                forma_pagamento=forma_pagamento
            )
            novas_vendas_db.append(nova_venda)

        # Adiciona tudo ao banco de dados
        db.session.add_all(novas_vendas_db)
        db.session.commit()
        
        return jsonify({'status': 'sucesso', 'mensagem': 'Venda finalizada!', 'id_pedido': novo_pedido_id}), 201

    except Exception as e:
        db.session.rollback() # Desfaz as alterações em caso de erro
        return jsonify({'erro': str(e)}), 400


# ROTA ADICIONADA (para página de relatórios)
@app.route('/relatorios', methods=['GET'])
def get_relatorio_dia():
    data_str = request.args.get('data')
    if not data_str:
        return jsonify({'erro': 'Parâmetro data (YYYY-MM-DD) é obrigatório'}), 400
        
    try:
        data_filtro = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    # 1. Vendas do dia (agrupadas por pedido)
    vendas_dia = db.session.query(
        Venda.id_pedido,
        Venda.cliente_cpf,
        Venda.hora_venda,
        Venda.forma_pagamento,
        func.sum(Venda.valor).label('valor_total')
    ).filter(Venda.data_venda == data_filtro)\
     .group_by(Venda.id_pedido, Venda.cliente_cpf, Venda.hora_venda, Venda.forma_pagamento)\
     .order_by(Venda.hora_venda.desc())\
     .all()

    # 2. Totais por forma de pagamento
    totais_pagamento = db.session.query(
        Venda.forma_pagamento,
        func.sum(Venda.valor).label('total')
    ).filter(Venda.data_venda == data_filtro)\
     .group_by(Venda.forma_pagamento)\
     .all()

    # 3. Top produtos (mais vendidos)
    top_produtos = db.session.query(
        Produto.nome_produto,
        func.sum(Venda.quantidade).label('total_quantidade')
    ).join(Produto, Venda.produto == Produto.id_produto)\
     .filter(Venda.data_venda == data_filtro)\
     .group_by(Produto.nome_produto)\
     .order_by(func.sum(Venda.quantidade).desc())\
     .limit(5)\
     .all()
     
    # 4. "Bottom" produtos (menos vendidos)
    bottom_produtos = db.session.query(
        Produto.nome_produto,
        func.sum(Venda.quantidade).label('total_quantidade')
    ).join(Produto, Venda.produto == Produto.id_produto)\
     .filter(Venda.data_venda == data_filtro)\
     .group_by(Produto.nome_produto)\
     .order_by(func.sum(Venda.quantidade).asc())\
     .limit(5)\
     .all()

    # Formatar resultados
    vendas_formatadas = [
        {
            'id_pedido': v.id_pedido,
            'cliente_cpf': v.cliente_cpf,
            'valor': float(v.valor_total),
            'hora': v.hora_venda.isoformat() if v.hora_venda else None
        } for v in vendas_dia
    ]
    
    totais_formatados = {
        'dinheiro': 0.0,
        'cartao': 0.0,
        'pix': 0.0,
        'geral': 0.0
    }
    for t in totais_pagamento:
        if t.forma_pagamento in totais_formatados:
            totais_formatados[t.forma_pagamento] = float(t.total)
        totais_formatados['geral'] += float(t.total)

    grafico_data = {
        'top': [{'nome': p.nome_produto, 'total': p.total_quantidade} for p in top_produtos],
        'bottom': [{'nome': p.nome_produto, 'total': p.total_quantidade} for p in bottom_produtos]
    }

    return jsonify({
        'vendas_dia': vendas_formatadas,
        'totais': totais_formatados,
        'grafico_data': grafico_data
    })
# =======================
# INICIALIZAÇÃO
# =======================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
