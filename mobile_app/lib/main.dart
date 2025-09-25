import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// Chrome/web => http://127.0.0.1:5000
// Android emulator => http://10.0.2.2:5000
const String kBaseUrl = String.fromEnvironment(
  'BACKEND_URL', defaultValue: 'http://10.0.2.2:5000',
);

void main() => runApp(const PeerMindApp());

class PeerMindApp extends StatelessWidget {
  const PeerMindApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'PeerMind',
        theme: ThemeData(useMaterial3: true),
        home: const ChatPage(),
      );
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});
  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _ctrl = TextEditingController();
  final _msgs = <_Msg>[];
  bool _busy = false;

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _busy) return;
    setState(() {
      _msgs.add(_Msg(text, true));
      _busy = true;
      _ctrl.clear();
    });

    try {
      final res = await http.post(
        Uri.parse('$kBaseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': text}),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);

        final reply = data['reply'] ?? '...';
        final emo = (data['analysis'] ?? {})['emotion'] ?? '';
        final conf = (data['analysis'] ?? {})['confidence']?.toString() ?? '';

        _msgs.add(_Msg(reply, false, emotion: emo, confidence: conf));
      } else {
        _msgs.add(_Msg('Error ${res.statusCode}', false));
      }
    } catch (e) {
      _msgs.add(_Msg('Network error: $e', false));
    } finally {
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('PeerMind (alpha)')),
        body: Column(children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: _msgs.length,
              itemBuilder: (_, i) {
                final m = _msgs[i];
                return Align(
                  alignment:
                      m.user ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: m.user
                          ? Colors.blue.shade100
                          : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(m.text),
                        if (!m.user && m.emotion.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              '(${m.emotion}, ${m.confidence})',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade600,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 6, 12, 12),
              child: Row(children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    onSubmitted: (_) => _send(),
                    decoration: const InputDecoration(
                      hintText: 'Type how you feel…',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: _busy ? null : _send,
                  child: _busy
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Send'),
                ),
              ]),
            ),
          ),
        ]),
      );
}

class _Msg {
  final String text;
  final bool user;
  final String emotion;
  final String confidence;

  _Msg(this.text, this.user, {this.emotion = '', this.confidence = ''});
}
