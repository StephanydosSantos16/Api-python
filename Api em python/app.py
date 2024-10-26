from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://stephany:12345@localhost/biblioteca'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_exist = Usuario.query.filter_by(username=username).first()
        if user_exist:
            flash('Usuário já existe!')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = Usuario(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('produtos'))
        else:
            flash('Credenciais incorretas!')

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/produtos', methods=['GET', 'POST'])
@login_required
def produtos():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        novo_produto = Produto(nome=nome, descricao=descricao, preco=preco, usuario_id=current_user.id)
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!')

    produtos = Produto.query.filter_by(usuario_id=current_user.id).all()
    return render_template('produtos.html', produtos=produtos)


@app.route('/produtos/<int:id>', methods=['GET'])
@login_required
def selecionar_produto(id):
    produto = Produto.query.get(id)
    if produto and produto.usuario_id == current_user.id:
        return render_template('detalhes_produto.html', produto=produto)
    else:
        flash('Produto não encontrado ou você não tem permissão para visualizá-lo.')
        return redirect(url_for('produtos'))

@app.route('/produtos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    produto = Produto.query.get(id)
    if produto.usuario_id != current_user.id:
        flash('Você não tem permissão para editar este produto!')
        return redirect(url_for('produtos'))

    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.descricao = request.form['descricao']
        produto.preco = request.form['preco']
        db.session.commit()
        flash('Produto editado com sucesso!')
        return redirect(url_for('produtos'))

    return render_template('editar_produto.html', produto=produto)

@app.route('/produtos/deletar/<int:id>', methods=['POST'])
@login_required
def deletar_produto(id):
    produto = Produto.query.get(id)
    if produto.usuario_id != current_user.id:
        flash('Você não tem permissão para deletar este produto!')
        return redirect(url_for('produtos'))

    db.session.delete(produto)
    db.session.commit()
    flash('Produto deletado com sucesso!')
    return redirect(url_for('produtos'))

if __name__ == '__main__':
    app.run(debug=True)
