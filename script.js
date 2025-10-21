// script.js

// URL base da sua API Flask
const API_URL = 'http://127.0.0.1:5000';

/**
 * Função utilitária para formatar valores monetários
 */
function formatarDinheiro(valor) {
    return Number(valor).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });
}

/**
 * Função utilitária para exibir modais
 */
function mostrarModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

/**
 * Função utilitária para esconder modais
 */
function esconderModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Função utilitária para configurar a abertura e fechamento de modais
 */
function configurarModal(btnId, modalId) {
    const btn = document.getElementById(btnId);
    const modal = document.getElementById(modalId);
    
    if (btn && modal) {
        // Abrir modal
        btn.addEventListener('click', () => mostrarModal(modalId));

        // Fechar modal ao clicar fora (no overlay)
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                esconderModal(modalId);
            }
        });
    }
}

/**
 * Função wrapper para chamadas fetch
 */
async function apiFetch(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        
        if (!response.ok) {
            const erroData = await response.json();
            throw new Error(erroData.erro || `Erro HTTP: ${response.status}`);
        }
        
        // Retorna JSON se houver conteúdo, senão retorna a resposta
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return await response.json();
        } else {
            return response;
        }
    } catch (error) {
        console.error('Erro na API:', error);
        alert(`Erro ao comunicar com o servidor: ${error.message}`);
        throw error; // Propaga o erro
    }
}


// --- INÍCIO DA LÓGICA DO SCRIPT ---
document.addEventListener('DOMContentLoaded', () => {
    
    const pagina = document.body.id;

    // --- LÓGICA GERAL (Modais) ---
    configurarModal('btn-novo-cliente', 'modal-novo-cliente');
    configurarModal('btn-novo-produto', 'modal-novo-produto');
    configurarModal('btn-nova-doca', 'modal-nova-doca');
    configurarModal('btn-nova-categoria', 'modal-nova-categoria');
    configurarModal('btn-editar-produto-modal', 'modal-editar-produto');
    configurarModal('btn-editar-cliente-modal', 'modal-editar-cliente');


    // --- PÁGINA 1: LOGIN ---
    if (document.getElementById('btn-entrar')) {
        document.getElementById('btn-entrar').addEventListener('click', async () => {
            const usuario = document.getElementById('usuario').value;
            const senha = document.getElementById('senha').value;
            
            if (!usuario || !senha) {
                alert('Por favor, preencha usuário e senha.');
                return;
            }
            
            try {
                const data = await apiFetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ usuario: usuario, senha: senha })
                });
                
                if (data.status === 'sucesso') {
                    // Simples verificação. Em um app real, usaríamos Tokens (JWT)
                    localStorage.setItem('usuarioLogado', 'true');
                    window.location.href = 'vendas.html';
                }
            } catch (error) {
                // 'apiFetch' já exibe um alerta de erro
            }
        });
    }
    
    // --- LÓGICA DE VERIFICAÇÃO DE LOGIN (para todas as páginas, exceto login) ---
    // Se não estiver na página de login E não tiver o item 'usuarioLogado'
    if (pagina !== 'pagina-login' && !localStorage.getItem('usuarioLogado')) {
        alert('Você precisa fazer login para acessar esta página.');
        window.location.href = 'login.html';
        return; // Para a execução do script
    }


    // --- PÁGINA 2: VENDAS ---
    if (pagina === 'pagina-vendas') {
        let carrinho = [];
        const pesquisaInput = document.getElementById('pesquisa-produto-venda');
        const autocompleteLista = document.getElementById('autocomplete-lista');
        const listaSelecionados = document.getElementById('produtos-selecionados-lista');
        const valorTotalEl = document.getElementById('valor-total');
        const btnFinalizar = document.getElementById('btn-finalizar-venda');

        // Pesquisa de produtos (autocomplete)
        pesquisaInput.addEventListener('input', async (e) => {
            const termo = e.target.value;
            autocompleteLista.innerHTML = ''; // Limpa resultados
            
            if (termo.length < 1) return;

            const produtos = await apiFetch(`/produtos/search?q=${termo}`);
            
            produtos.forEach(produto => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';
                div.innerHTML = `(${produto.id_produto}) ${produto.nome_produto} - ${formatarDinheiro(produto.valor)} (Estoque: ${produto.quantidade})`;
                div.onclick = () => adicionarAoCarrinho(produto);
                autocompleteLista.appendChild(div);
            });
        });

        const adicionarAoCarrinho = (produto) => {
            if (produto.quantidade <= 0) {
                alert('Produto sem estoque!');
                return;
            }
            
            const itemExistente = carrinho.find(item => item.id_produto === produto.id_produto);
            
            if (itemExistente) {
                if(itemExistente.quantidade < produto.quantidade) {
                    itemExistente.quantidade++;
                } else {
                    alert('Quantidade máxima em estoque atingida.');
                }
            } else {
                carrinho.push({ ...produto, quantidade: 1 });
            }
            
            pesquisaInput.value = '';
            autocompleteLista.innerHTML = '';
            renderizarCarrinho();
        };

        const renderizarCarrinho = () => {
            listaSelecionados.innerHTML = '';
            let total = 0;
            
            if (carrinho.length === 0) {
                 listaSelecionados.innerHTML = '<p>Nenhum produto selecionado.</p>';
            }
            
            carrinho.forEach(item => {
                const itemTotal = item.valor * item.quantidade;
                total += itemTotal;
                
                const div = document.createElement('div');
                div.className = 'item-carrinho';
                div.innerHTML = `
                    <span>(${item.id_produto}) ${item.nome_produto}</span>
                    <input type="number" value="${item.quantidade}" min="1" max="${item.quantidade}" 
                           data-id="${item.id_produto}" class="input-qtd-carrinho">
                    <strong>${formatarDinheiro(itemTotal)}</strong>
                    <button class="btn-remover-carrinho" data-id="${item.id_produto}">❌</button>
                `;
                listaSelecionados.appendChild(div);
            });
            
            valorTotalEl.textContent = formatarDinheiro(total);
        };

        // Event listener para atualizar quantidade ou remover
        listaSelecionados.addEventListener('change', (e) => {
            if (e.target.classList.contains('input-qtd-carrinho')) {
                const id = Number(e.target.dataset.id);
                let novaQtd = Number(e.target.value);
                
                const item = carrinho.find(item => item.id_produto === id);
                const produtoOriginal = item; // O 'item' no carrinho já tem o estoque
                
                if (novaQtd > produtoOriginal.quantidade) {
                    alert(`Estoque máximo é ${produtoOriginal.quantidade}`);
                    novaQtd = produtoOriginal.quantidade;
                    e.target.value = novaQtd;
                }
                
                if (novaQtd < 1) {
                    novaQtd = 1;
                    e.target.value = 1;
                }
                
                item.quantidade = novaQtd;
                renderizarCarrinho();
            }
        });
        
        listaSelecionados.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-remover-carrinho')) {
                const id = Number(e.target.dataset.id);
                carrinho = carrinho.filter(item => item.id_produto !== id);
                renderizarCarrinho();
            }
        });

        // Adicionar novo cliente (modal)
        document.getElementById('btn-add-cliente').addEventListener('click', async () => {
            const cpf = document.getElementById('cliente-cpf-modal').value;
            const nome = document.getElementById('cliente-nome-modal').value;
            const telefone = document.getElementById('cliente-telefone-modal').value;
            
            if (!cpf || !nome) {
                alert('CPF e Nome são obrigatórios.');
                return;
            }
            
            try {
                await apiFetch('/clientes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cpf: cpf, nome_cliente: nome, telefone: telefone })
                });
                alert('Cliente adicionado com sucesso!');
                esconderModal('modal-novo-cliente');
                document.getElementById('form-novo-cliente').reset(); // Limpa o formulário
            } catch (error) { /* erro já tratado pelo apiFetch */ }
        });

        // Finalizar Venda
        btnFinalizar.addEventListener('click', async () => {
            if (carrinho.length === 0) {
                alert('Adicione produtos ao carrinho para finalizar a venda.');
                return;
            }
            
            const forma_pagamento = document.getElementById('forma-pagamento').value;
            const cliente_cpf = document.getElementById('cliente-cpf').value;

            const dadosVenda = {
                forma_pagamento: forma_pagamento,
                cliente_cpf: cliente_cpf || null,
                // Enviamos apenas os dados essenciais do carrinho
                produtos: carrinho.map(item => ({
                    id_produto: item.id_produto,
                    quantidade: item.quantidade,
                    valor: item.valor // Valor unitário
                }))
            };
            
            try {
                const resultado = await apiFetch('/vendas/finalizar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dadosVenda)
                });
                
                alert(`Venda (Pedido ${resultado.id_pedido}) finalizada com sucesso!`);
                carrinho = [];
                renderizarCarrinho();
                document.getElementById('cliente-cpf').value = '';
                
            } catch (error) { /* erro já tratado */ }
        });
    }

    // --- PÁGINA 3: PRODUTOS ---
    if (pagina === 'pagina-produtos') {
        const listaProdutosEl = document.getElementById('lista-produtos');
        const pesquisaInput = document.getElementById('pesquisa-produto');
        let todosProdutos = []; // Cache local para pesquisa

        const carregarProdutos = async () => {
            try {
                todosProdutos = await apiFetch('/produtos');
                renderizarProdutos(todosProdutos);
            } catch (error) {}
        };
        
        const renderizarProdutos = (produtos) => {
            listaProdutosEl.innerHTML = '';
            produtos.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${p.id_produto}</td>
                    <td>${p.nome_produto}</td>
                    <td>${formatarDinheiro(p.valor)}</td>
                    <td>${p.quantidade}</td>
                    <td>${p.doca || 'N/A'}</td>
                    <td>
                        <span class="action-icon" data-action="edit" data-id="${p.id_produto}">✏️</span>
                        <span class="action-icon" data-action="delete" data-id="${p.id_produto}">🗑️</span>
                    </td>
                `;
                listaProdutosEl.appendChild(tr);
            });
        };

        // Pesquisa local
        pesquisaInput.addEventListener('input', (e) => {
            const termo = e.target.value.toLowerCase();
            const filtrados = todosProdutos.filter(p => 
                p.nome_produto.toLowerCase().includes(termo) ||
                String(p.id_produto).includes(termo)
            );
            renderizarProdutos(filtrados);
        });

        // Adicionar novo produto
        document.getElementById('btn-add-produto').addEventListener('click', async () => {
            // Coleta de dados do modal
            const dadosProduto = {
                id_produto: document.getElementById('produto-id').value,
                nome_produto: document.getElementById('produto-nome').value,
                valor: document.getElementById('produto-valor').value,
                quantidade: document.getElementById('produto-qtd').value,
                lote: document.getElementById('produto-lote').value,
                categoria: document.getElementById('produto-categoria').value,
                fornecedor: document.getElementById('produto-fornecedor').value,
                doca: document.getElementById('produto-doca').value,
                validade: '2025-12-31' // CAMPO 'validade' ESTÁ FALTANDO NO SEU MODAL! Adicionando um fixo.
            };
            
            // TODO: Adicionar o campo 'validade' (tipo date) no seu modal-novo-produto
            
            try {
                await apiFetch('/produtos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dadosProduto)
                });
                alert('Produto adicionado com sucesso!');
                esconderModal('modal-novo-produto');
                document.getElementById('form-novo-produto').reset();
                carregarProdutos(); // Recarrega a lista
            } catch (error) {}
        });
        
        // Ações de Editar / Deletar
        listaProdutosEl.addEventListener('click', async (e) => {
            if (!e.target.classList.contains('action-icon')) return;
            
            const action = e.target.dataset.action;
            const id = e.target.dataset.id;
            
            if (action === 'delete') {
                if (confirm('Tem certeza que deseja deletar este produto?')) {
                    try {
                        await apiFetch(`/produtos/${id}`, { method: 'DELETE' });
                        alert('Produto deletado com sucesso!');
                        carregarProdutos();
                    } catch (error) {}
                }
            }
            
            if (action === 'edit') {
                // (Lógica para abrir modal de edição)
                alert(`Função "Editar" (ID: ${id}) não implementada neste exemplo.`);
                // 1. Buscar dados do produto: await apiFetch(`/produtos/${id}`)
                // 2. Preencher o modal 'modal-editar-produto' com os dados
                // 3. MostrarModal('modal-editar-produto')
                // 4. No botão 'salvar' do modal, fazer um PUT: await apiFetch(`/produtos/${id}`, { method: 'PUT', ... })
            }
        });

        carregarProdutos(); // Carga inicial
    }

    // --- PÁGINA 4: RELATÓRIOS ---
    if (pagina === 'pagina-relatorios') {
        const calendario = document.getElementById('calendario-relatorio');
        const dataAtualEl = document.getElementById('data-atual');
        const canvas = document.getElementById('grafico-vendas');
        let meuGrafico = null; // Variável para armazenar a instância do gráfico
        
        // Define a data de hoje no calendário
        const hoje = new Date().toISOString().split('T')[0];
        calendario.value = hoje;
        dataAtualEl.textContent = new Date().toLocaleDateString('pt-BR', { dateStyle: 'long' });
        
        const carregarRelatorio = async (data) => {
            try {
                const relatorio = await apiFetch(`/relatorios?data=${data}`);
                
                // 1. Preencher Totais
                document.getElementById('total-dinheiro').textContent = formatarDinheiro(relatorio.totais.dinheiro);
                document.getElementById('total-cartao').textContent = formatarDinheiro(relatorio.totais.cartao);
                document.getElementById('total-pix').textContent = formatarDinheiro(relatorio.totais.pix);
                document.getElementById('total-geral').textContent = formatarDinheiro(relatorio.totais.geral);
                
                // 2. Preencher Cards de Vendas
                const listaVendasEl = document.getElementById('vendas-dia-lista');
                listaVendasEl.innerHTML = '';
                if (relatorio.vendas_dia.length === 0) {
                    listaVendasEl.innerHTML = '<p>Nenhuma venda encontrada para esta data.</p>';
                } else {
                    relatorio.vendas_dia.forEach(venda => {
                        const card = document.createElement('div');
                        card.className = 'venda-card';
                        card.innerHTML = `
                            <div class="id-venda">Pedido: ${venda.id_pedido}</div>
                            <div class="cliente-cpf">CPF: ${venda.cliente_cpf || 'Não informado'}</div>
                            <div class="valor">${formatarDinheiro(venda.valor)}</div>
                            <div class="hora">${venda.hora}</div>
                        `;
                        listaVendasEl.appendChild(card);
                    });
                }
                
                // 3. Renderizar Gráfico
                renderizarGrafico(relatorio.grafico_data);
                
            } catch (error) {}
        };
        
        const renderizarGrafico = (data) => {
            const ctx = canvas.getContext('2d');
            
            // Combina top 5 e bottom 5
            const labels = [
                ...data.top.map(p => p.nome),
                ...data.bottom.map(p => p.nome)
            ];
            const valores = [
                ...data.top.map(p => p.total),
                ...data.bottom.map(p => p.total * -1) // Negativo para "Bottom"
            ];
            
            // Destrói gráfico anterior se existir
            if (meuGrafico) {
                meuGrafico.destroy();
            }
            
            meuGrafico = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Quantidade Vendida (Positivo = Mais, Negativo = Menos)',
                        data: valores,
                        backgroundColor: valores.map(v => v > 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)'),
                        borderColor: valores.map(v => v > 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)'),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'Produtos Mais e Menos Vendidos' }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        };

        // Event listener para mudança de data
        calendario.addEventListener('change', (e) => {
            const novaData = e.target.value;
            const dataObj = new Date(novaData + 'T12:00:00'); // Fuso horário
            dataAtualEl.textContent = dataObj.toLocaleDateString('pt-BR', { dateStyle: 'long' });
            carregarRelatorio(novaData);
        });
        
        // Carga inicial
        carregarRelatorio(hoje);
    }
    
    // --- PÁGINA 5: CLIENTES ---
    if (pagina === 'pagina-clientes') {
        const listaClientesEl = document.getElementById('lista-clientes');
        const pesquisaInput = document.getElementById('pesquisa-cliente');

        const carregarClientes = async (termo = '') => {
            try {
                // Usamos a nova rota de busca
                const clientes = await apiFetch(`/clientes/search?q=${termo}`);
                renderizarClientes(clientes);
            } catch (error) {}
        };
        
        const renderizarClientes = (clientes) => {
            listaClientesEl.innerHTML = '';
            clientes.forEach(c => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${c.cpf}</td>
                    <td>${c.nome_cliente}</td>
                    <td>${c.telefone || 'N/A'}</td>
                    <td>
                        <span class="action-icon" data-action="edit" data-cpf="${c.cpf}">✏️</span>
                    </td>
                `;
                listaClientesEl.appendChild(tr);
            });
        };

        // Pesquisa (com delay para não sobrecarregar API)
        let searchTimeout;
        pesquisaInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const termo = e.target.value;
            searchTimeout = setTimeout(() => {
                carregarClientes(termo);
            }, 300); // Espera 300ms
        });
        
        // (Lógica de Edição - não implementada, similar à de produtos)
        listaClientesEl.addEventListener('click', (e) => {
             if (e.target.dataset.action === 'edit') {
                 alert('Modal de edição de cliente não implementado.');
             }
        });

        carregarClientes(); // Carga inicial
    }
    
    // --- PÁGINA 6: DOCAS ---
    if (pagina === 'pagina-docas') {
        const listaDocasEl = document.getElementById('lista-docas');
        const pesquisaInput = document.getElementById('pesquisa-doca');

        const carregarDocas = async (termo = '') => {
            try {
                // Usamos a nova rota que já traz os produtos
                const docas = await apiFetch(`/docas/produtos?q=${termo}`);
                renderizarDocas(docas);
            } catch (error) {}
        };
        
        const renderizarDocas = (docas) => {
            listaDocasEl.innerHTML = '';
            docas.forEach(d => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${d.doca}</td>
                    <td>${d.id_produto || '---'}</td>
                    <td>${d.nome_produto}</td>
                    <td>
                        </td>
                `;
                listaDocasEl.appendChild(tr);
            });
        };

        // Pesquisa
        let searchTimeout;
        pesquisaInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const termo = e.target.value;
            searchTimeout = setTimeout(() => {
                carregarDocas(termo);
            }, 300);
        });
        
        // Adicionar nova doca
        document.getElementById('btn-add-doca').addEventListener('click', async () => {
             const id_doca = document.getElementById('doca-id-modal').value;
             if (!id_doca) {
                 alert('ID da Doca é obrigatório.');
                 return;
             }
             try {
                await apiFetch('/docas', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_doca: id_doca })
                });
                alert('Doca criada com sucesso!');
                esconderModal('modal-nova-doca');
                document.getElementById('form-nova-doca').reset();
                carregarDocas();
             } catch (error) {}
        });

        carregarDocas(); // Carga inicial
    }
    
    // --- PÁGINA 7: CATEGORIAS ---
    if (pagina === 'pagina-categorias') {
        const listaCategoriasEl = document.getElementById('lista-categorias');
        const pesquisaInput = document.getElementById('pesquisa-categoria');

        const carregarCategorias = async (termo = '') => {
            try {
                // Usamos a nova rota que já traz os produtos
                const categorias = await apiFetch(`/categorias/produtos?q=${termo}`);
                renderizarCategorias(categorias);
            } catch (error) {}
        };
        
        const renderizarCategorias = (categorias) => {
            listaCategoriasEl.innerHTML = '';
            categorias.forEach(c => {
                const div = document.createElement('div');
                div.className = 'categoria-item';
                
                let produtosHtml = '';
                if (c.produtos.length > 0) {
                    c.produtos.forEach(p => {
                        produtosHtml += `
                            <div class="produto-item">
                                <span>(${p.id_produto}) ${p.nome_produto} - Qtd: ${p.quantidade}</span>
                                <span class="action-icon" data-action="remove" data-id="${p.id_produto}">❌</span>
                            </div>
                        `;
                    });
                } else {
                    produtosHtml = '<p>Nenhum produto nesta categoria.</p>';
                }

                div.innerHTML = `
                    <h3>${c.nome_categoria} (ID: ${c.id_categoria})</h3>
                    <div class="produtos-da-categoria">
                        ${produtosHtml}
                    </div>
                `;
                listaCategoriasEl.appendChild(div);
            });
        };

        // Pesquisa
        let searchTimeout;
        pesquisaInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const termo = e.target.value;
            searchTimeout = setTimeout(() => {
                carregarCategorias(termo);
            }, 300);
        });
        
        // Adicionar nova categoria
        document.getElementById('btn-add-categoria').addEventListener('click', async () => {
            const id_categoria = document.getElementById('categoria-id-modal').value;
            const nome_categoria = document.getElementById('categoria-nome-modal').value;

            if (!id_categoria || !nome_categoria) {
                alert('ID e Nome são obrigatórios.');
                return;
            }
             
            try {
                await apiFetch('/categorias', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_categoria, nome_categoria })
                });
                alert('Categoria criada com sucesso!');
                esconderModal('modal-nova-categoria');
                document.getElementById('form-nova-categoria').reset();
                carregarCategorias();
            } catch(error) {}
        });

        // Expandir / Remover produto (Ação 'remover' desvincula o produto)
        listaCategoriasEl.addEventListener('click', (e) => {
            // Expande/recolhe
            const header = e.target.closest('h3');
            if (header) {
                const produtosDiv = header.nextElementSibling;
                produtosDiv.style.display = produtosDiv.style.display === 'block' ? 'none' : 'block';
                return;
            }
            
            // Remove produto da categoria (coloca categoria como NULL)
            if (e.target.dataset.action === 'remove') {
                const idProduto = e.target.dataset.id;
                if (confirm('Deseja remover este produto desta categoria? (Ele não será deletado, apenas desvinculado)')) {
                    // Esta lógica requer atualizar o produto
                    // await apiFetch(`/produtos/${idProduto}`, { method: 'PUT', body: JSON.stringify({ categoria: null }) })
                    alert(`(Simulação) Produto ${idProduto} removido da categoria.`);
                    // carregarCategorias(); // Recarrega
                }
            }
        });

        carregarCategorias(); // Carga inicial
    }

}); // Fim do DOMContentLoaded