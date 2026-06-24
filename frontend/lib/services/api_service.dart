import 'dart:io';
import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../config/constants.dart';
import '../models/generation_result.dart';
import '../models/scenario.dart';

class ApiService {
  late final Dio _dio;

  ApiService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(minutes: 3),
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final user = FirebaseAuth.instance.currentUser;
          if (user != null) {
            final token = await user.getIdToken();
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
  }

  Future<GenerationResult> generateImage({
    required File imageFile,
    required Scenario scenario,
    String? customPrompt,
  }) async {
    final user = FirebaseAuth.instance.currentUser;

    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(
        imageFile.path,
        filename: 'photo.jpg',
      ),
      'scenario': scenario.apiValue,
      if (customPrompt != null && customPrompt.isNotEmpty)
        'prompt': customPrompt,
      if (user != null) 'user_id': user.uid,
    });

    final response = await _dio.post(
      AppConstants.generateEndpoint,
      data: formData,
    );

    return GenerationResult.fromJson(response.data as Map<String, dynamic>);
  }

  Future<bool> healthCheck() async {
    try {
      final response = await _dio.get(
        '${AppConstants.apiBaseUrl.replaceAll('/api/v1', '')}/health',
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
