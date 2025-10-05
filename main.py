from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
from decimal import Decimal
from dotenv import load_dotenv
import os

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
    
    def to_dict(self):
        return {
            'cpf': self.cpf,
            'nome_cliente': self.nome_cliente
        }

class Doca(db.Model):
    __tablename__ = 'docas'
    id_doca = db.Column(db.Integer, primary_key=True)
    produto = db.Column(db.Integer, db.ForeignKey('produtos.id_produto'))
    
    produto_obj = db.relationship('Produto', foreign_keys='Doca.produto', backref='docas_produtos')
    
    def to_dict(self):
        return {
            'id_doca': self.id_doca,
            'produto': self.produto
        }

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
            'valor': float(self.valor)
        }

class Venda(db.Model):
    __tablename__ = 'vendas'
    id_venda = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    produto = db.Column(db.Integer, db.ForeignKey('produtos.id_produto'), nullable=False)
    cliente_cpf = db.Column(db.BigInteger, db.ForeignKey('clientes.cpf'))
    data_venda = db.Column(db.Date, nullable=False)
    
    produto_obj = db.relationship('Produto')
    cliente_obj = db.relationship('Cliente')
    
    def to_dict(self):
        return {
            'id_venda': self.id_venda,
            'valor': float(self.valor),
            'quantidade': self.quantidade,
            'produto': self.produto,
            'cliente_cpf': self.cliente_cpf,
            'data_venda': self.data_venda.isoformat() if self.data_venda else None
        }

# =======================
# ROTAS - HOME
# =======================

@app.route('/')
def home():
    return jsonify({
        'mensagem': 'API de Gerenciamento de Estoque',
        'endpoints': {
            'categorias': '/categorias',
            'fornecedores': '/fornecedores',
            'clientes': '/clientes',
            'produtos': '/produtos',
            'docas': '/docas',
            'vendas': '/vendas'
        }
    })

# =======================
# ROTAS - CATEGORIAS
# =======================

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    categorias = Categoria.query.all()
    return jsonify([c.to_dict() for c in categorias])

@app.route('/categorias/<int:id>', methods=['GET'])
def buscar_categoria(id):
    categoria = Categoria.query.get(id)
    if not categoria:
        return jsonify({'erro': 'Categoria não encontrada'}), 404
    return jsonify(categoria.to_dict())

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

@app.route('/categorias/<int:id>', methods=['PUT'])
def atualizar_categoria(id):
    categoria = Categoria.query.get(id)
    if not categoria:
        return jsonify({'erro': 'Categoria não encontrada'}), 404
    
    dados = request.get_json()
    if dados.get('nome_categoria'):
        categoria.nome_categoria = dados['nome_categoria']
    
    db.session.commit()
    return jsonify(categoria.to_dict())

@app.route('/categorias/<int:id>', methods=['DELETE'])
def deletar_categoria(id):
    categoria = Categoria.query.get(id)
    if not categoria:
        return jsonify({'erro': 'Categoria não encontrada'}), 404
    
    db.session.delete(categoria)
    db.session.commit()
    return jsonify({'mensagem': 'Categoria deletada com sucesso'})

# =======================
# ROTAS - FORNECEDORES
# =======================

@app.route('/fornecedores', methods=['GET'])
def listar_fornecedores():
    fornecedores = Fornecedor.query.all()
    return jsonify([f.to_dict() for f in fornecedores])

@app.route('/fornecedores/<int:cnpj>', methods=['GET'])
def buscar_fornecedor(cnpj):
    fornecedor = Fornecedor.query.get(cnpj)
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404
    return jsonify(fornecedor.to_dict())

@app.route('/fornecedores', methods=['POST'])
def criar_fornecedor():
    dados = request.get_json()
    if not dados.get('cnpj') or not dados.get('nome_empresa'):
        return jsonify({'erro': 'cnpj e nome_empresa são obrigatórios'}), 400
    
    novo_fornecedor = Fornecedor(
        cnpj=dados['cnpj'],
        nome_empresa=dados['nome_empresa'],
        categoria=dados.get('categoria')
    )
    db.session.add(novo_fornecedor)
    db.session.commit()
    return jsonify(novo_fornecedor.to_dict()), 201

@app.route('/fornecedores/<int:cnpj>', methods=['PUT'])
def atualizar_fornecedor(cnpj):
    fornecedor = Fornecedor.query.get(cnpj)
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404
    
    dados = request.get_json()
    if dados.get('nome_empresa'):
        fornecedor.nome_empresa = dados['nome_empresa']
    if dados.get('categoria'):
        fornecedor.categoria = dados['categoria']
    
    db.session.commit()
    return jsonify(fornecedor.to_dict())

@app.route('/fornecedores/<int:cnpj>', methods=['DELETE'])
def deletar_fornecedor(cnpj):
    fornecedor = Fornecedor.query.get(cnpj)
    if not fornecedor:
        return jsonify({'erro': 'Fornecedor não encontrado'}), 404
    
    db.session.delete(fornecedor)
    db.session.commit()
    return jsonify({'mensagem': 'Fornecedor deletado com sucesso'})

# =======================
# ROTAS - CLIENTES
# =======================

@app.route('/clientes', methods=['GET'])
def listar_clientes():
    clientes = Cliente.query.all()
    return jsonify([c.to_dict() for c in clientes])

@app.route('/clientes/<int:cpf>', methods=['GET'])
def buscar_cliente(cpf):
    cliente = Cliente.query.get(cpf)
    if not cliente:
        return jsonify({'erro': 'Cliente não encontrado'}), 404
    return jsonify(cliente.to_dict())

@app.route('/clientes', methods=['POST'])
def criar_cliente():
    dados = request.get_json()
    if not dados.get('cpf') or not dados.get('nome_cliente'):
        return jsonify({'erro': 'cpf e nome_cliente são obrigatórios'}), 400
    
    novo_cliente = Cliente(
        cpf=dados['cpf'],
        nome_cliente=dados['nome_cliente']
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
    
    db.session.commit()
    return jsonify(cliente.to_dict())

@app.route('/clientes/<int:cpf>', methods=['DELETE'])
def deletar_cliente(cpf):
    cliente = Cliente.query.get(cpf)
    if not cliente:
        return jsonify({'erro': 'Cliente não encontrado'}), 404
    
    db.session.delete(cliente)
    db.session.commit()
    return jsonify({'mensagem': 'Cliente deletado com sucesso'})

# =======================
# ROTAS - DOCAS
# =======================

@app.route('/docas', methods=['GET'])
def listar_docas():
    docas = Doca.query.all()
    return jsonify([d.to_dict() for d in docas])

@app.route('/docas/<int:id>', methods=['GET'])
def buscar_doca(id):
    doca = Doca.query.get(id)
    if not doca:
        return jsonify({'erro': 'Doca não encontrada'}), 404
    return jsonify(doca.to_dict())

@app.route('/docas', methods=['POST'])
def criar_doca():
    dados = request.get_json()
    if not dados.get('id_doca'):
        return jsonify({'erro': 'id_doca é obrigatório'}), 400
    
    nova_doca = Doca(
        id_doca=dados['id_doca'],
        produto=dados.get('produto')
    )
    db.session.add(nova_doca)
    db.session.commit()
    return jsonify(nova_doca.to_dict()), 201

@app.route('/docas/<int:id>', methods=['PUT'])
def atualizar_doca(id):
    doca = Doca.query.get(id)
    if not doca:
        return jsonify({'erro': 'Doca não encontrada'}), 404
    
    dados = request.get_json()
    if 'produto' in dados:
        doca.produto = dados['produto']
    
    db.session.commit()
    return jsonify(doca.to_dict())

@app.route('/docas/<int:id>', methods=['DELETE'])
def deletar_doca(id):
    doca = Doca.query.get(id)
    if not doca:
        return jsonify({'erro': 'Doca não encontrada'}), 404
    
    db.session.delete(doca)
    db.session.commit()
    return jsonify({'mensagem': 'Doca deletada com sucesso'})

# =======================
# ROTAS - PRODUTOS
# =======================

@app.route('/produtos', methods=['GET'])
def listar_produtos():
    produtos = Produto.query.all()
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
    campos_obrigatorios = ['id_produto', 'nome_produto', 'validade', 'lote', 'categoria', 'fornecedor', 'valor']
    
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
        valor=dados['valor']
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
    
    db.session.commit()
    return jsonify(produto.to_dict())

@app.route('/produtos/<int:id>', methods=['DELETE'])
def deletar_produto(id):
    produto = Produto.query.get(id)
    if not produto:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    
    db.session.delete(produto)
    db.session.commit()
    return jsonify({'mensagem': 'Produto deletado com sucesso'})

# =======================
# ROTAS - VENDAS
# =======================

@app.route('/vendas', methods=['GET'])
def listar_vendas():
    vendas = Venda.query.all()
    return jsonify([v.to_dict() for v in vendas])

@app.route('/vendas/<int:id>', methods=['GET'])
def buscar_venda(id):
    venda = Venda.query.get(id)
    if not venda:
        return jsonify({'erro': 'Venda não encontrada'}), 404
    return jsonify(venda.to_dict())

@app.route('/vendas', methods=['POST'])
def criar_venda():
    dados = request.get_json()
    campos_obrigatorios = ['id_venda', 'valor', 'quantidade', 'produto', 'data_venda']
    
    for campo in campos_obrigatorios:
        if campo not in dados:
            return jsonify({'erro': f'{campo} é obrigatório'}), 400
    
    nova_venda = Venda(
        id_venda=dados['id_venda'],
        valor=dados['valor'],
        quantidade=dados['quantidade'],
        produto=dados['produto'],
        cliente_cpf=dados.get('cliente_cpf'),
        data_venda=datetime.strptime(dados['data_venda'], '%Y-%m-%d').date()
    )
    db.session.add(nova_venda)
    db.session.commit()
    return jsonify(nova_venda.to_dict()), 201

@app.route('/vendas/<int:id>', methods=['PUT'])
def atualizar_venda(id):
    venda = Venda.query.get(id)
    if not venda:
        return jsonify({'erro': 'Venda não encontrada'}), 404
    
    dados = request.get_json()
    if dados.get('valor'):
        venda.valor = dados['valor']
    if dados.get('quantidade'):
        venda.quantidade = dados['quantidade']
    if dados.get('produto'):
        venda.produto = dados['produto']
    if 'cliente_cpf' in dados:
        venda.cliente_cpf = dados['cliente_cpf']
    if dados.get('data_venda'):
        venda.data_venda = datetime.strptime(dados['data_venda'], '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify(venda.to_dict())

@app.route('/vendas/<int:id>', methods=['DELETE'])
def deletar_venda(id):
    venda = Venda.query.get(id)
    if not venda:
        return jsonify({'erro': 'Venda não encontrada'}), 404
    
    db.session.delete(venda)
    db.session.commit()
    return jsonify({'mensagem': 'Venda deletada com sucesso'})

# =======================
# INICIALIZAÇÃO
# =======================

if __name__ == '__main__':
    app.run(debug=True, port=5000)