import 'dart:io';
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:dio/dio.dart';
import '../../models/generation_result.dart';

class ResultScreen extends StatefulWidget {
  final GenerationResult result;
  final String originalImagePath;

  const ResultScreen({
    super.key,
    required this.result,
    required this.originalImagePath,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _downloading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  bool get _isDataUri => widget.result.imageUrl.startsWith('data:image');

  Future<void> _download() async {
    setState(() => _downloading = true);
    try {
      final dir = await getApplicationDocumentsDirectory();
      final fileName = 'moda_ia_${DateTime.now().millisecondsSinceEpoch}.jpg';
      final filePath = '${dir.path}/$fileName';

      if (_isDataUri) {
        // Data URI — extract base64 and write directly
        final b64 = widget.result.imageUrl.split(',').last;
        final bytes = Uri.parse(
                'data:application/octet-stream;base64,$b64')
            .data!
            .contentAsBytes();
        await File(filePath).writeAsBytes(bytes);
      } else {
        final dio = Dio();
        await dio.download(widget.result.imageUrl, filePath);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imagem salva em $fileName'),
            behavior: SnackBarBehavior.floating,
            action: SnackBarAction(
              label: 'Compartilhar',
              onPressed: () => _share(filePath),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erro ao baixar: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  Future<void> _share(String filePath) async {
    await Share.shareXFiles([XFile(filePath)],
        text: 'Gerado com Moda IA 🎨');
  }

  Widget _buildGeneratedImage() {
    if (_isDataUri) {
      final b64 = widget.result.imageUrl.split(',').last;
      final bytes = Uri.parse(
              'data:application/octet-stream;base64,$b64')
          .data!
          .contentAsBytes();
      return Image.memory(bytes, fit: BoxFit.contain);
    }
    return CachedNetworkImage(
      imageUrl: widget.result.imageUrl,
      fit: BoxFit.contain,
      placeholder: (_, __) => const Center(child: CircularProgressIndicator()),
      errorWidget: (_, __, ___) => const Center(
        child: Icon(Icons.broken_image, size: 64),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Resultado'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => context.go('/home'),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () async {
              final dir = await getTemporaryDirectory();
              final tmpFile =
                  '${dir.path}/share_${DateTime.now().millisecondsSinceEpoch}.jpg';
              if (_isDataUri) {
                final b64 = widget.result.imageUrl.split(',').last;
                final bytes = Uri.parse(
                        'data:application/octet-stream;base64,$b64')
                    .data!
                    .contentAsBytes();
                await File(tmpFile).writeAsBytes(bytes);
              } else {
                await Dio().download(widget.result.imageUrl, tmpFile);
              }
              await _share(tmpFile);
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Antes'),
            Tab(text: 'Depois'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Image comparison
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                // Before
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.file(
                      File(widget.originalImagePath),
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
                // After
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: _buildGeneratedImage(),
                  ),
                ),
              ],
            ),
          ),
          // Info chip
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Icon(Icons.auto_awesome, size: 16, color: scheme.primary),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Cenário: ${widget.result.scenario.replaceAll('_', ' ')}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                  ),
                ),
              ],
            ),
          ),
          // Swipe hint
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.swipe, size: 16, color: scheme.onSurfaceVariant),
                const SizedBox(width: 6),
                Text(
                  'Deslize para comparar',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.onSurfaceVariant,
                      ),
                ),
              ],
            ),
          ),
          // Action buttons
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              children: [
                FilledButton.icon(
                  onPressed: _downloading ? null : _download,
                  icon: _downloading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.download),
                  label:
                      Text(_downloading ? 'Baixando...' : 'Baixar imagem'),
                  style: FilledButton.styleFrom(
                    minimumSize: const Size.fromHeight(52),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () => context.go('/upload'),
                  icon: const Icon(Icons.add_a_photo),
                  label: const Text('Gerar nova imagem'),
                  style: OutlinedButton.styleFrom(
                    minimumSize: const Size.fromHeight(52),
                  ),
                ),
                const SizedBox(height: 8),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
